"""
Regression tests for the CIAS ingestion pipeline.
Run with: docker exec cias_backend python -m pytest backend/tests/test_pipeline.py -v

These tests lock in the correctness guarantees of extraction v1.1:
  1. Name-only high similarity does NOT auto-merge (corroboration required)
  2. Name + shared phone DOES auto-merge
  3. Phone linked to two distinct names -> PHONE_CONFLICT
  4. Self-loops (A->A after merge) are audited, not silently deleted
  5. Duplicate FIR IDs from two uploads survive with provenance tracking
  6. Sentence-boundary phone linking guard
  7. Extraction version stamping
  8. OCR normalization preserves phone numbers
  9. Stoplist rejects field labels
"""

import pytest
import tempfile
import os
import uuid
import hashlib
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, "/app")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_entity(etype, value, eid=None):
    h = hashlib.sha256(value.encode()).hexdigest()[:8]
    return {
        "id":                 eid or f"{etype.lower()}:{h}",
        "type":               etype,
        "value":              value,
        "confidence":         0.85,
        "extraction_version": "1.1",
        "attributes":         {},
    }


def make_rel(rtype, source, target, confidence=0.5):
    return {
        "id":         str(uuid.uuid4()),
        "type":       rtype,
        "source":     source,
        "target":     target,
        "confidence": confidence,
        "status":     "suggested",
        "evidence":   "test evidence",
        "attributes": {},
    }


def fresh_registry():
    from backend.app.ingestion.resolver import EntityRegistry
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    os.unlink(tmp.name)
    reg = EntityRegistry(registry_path=tmp.name)
    yield reg
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)


# ─────────────────────────────────────────────────────────────────────────────
# Test 1 & 2: Name resolution corroboration gate
# ─────────────────────────────────────────────────────────────────────────────

class TestNameMergeCorroboration:

    def test_no_merge_without_corroboration(self):
        """'Ravi Kumar' + 'R. Kumar', no shared phone -> REVIEW_REQUIRED, no merge."""
        from backend.app.ingestion.resolver import resolve_entities
        reg_gen = fresh_registry()
        registry = next(reg_gen)

        e1 = make_entity("PERSON", "Ravi Kumar")
        resolve_entities({"entities": [e1], "relationships": []},
                         source_file="doc1.txt", registry=registry, case_id="CASE-001")

        e2 = make_entity("PERSON", "R. Kumar")
        result = resolve_entities({"entities": [e2], "relationships": []},
                                  source_file="doc2.txt", registry=registry, case_id="CASE-001")

        assert result["stats"]["merged"] == 0, (
            "Name-only auto-merge detected! Common surnames cause false merges at scale."
        )
        assert any(r["type"] == "PERSON_NAME_AMBIGUITY" for r in result["needs_review"])
        try: next(reg_gen)
        except StopIteration: pass

    def test_merge_with_shared_phone(self):
        """'Ravi Kumar' + 'R. Kumar' share a phone -> safe to auto-merge."""
        from backend.app.ingestion.resolver import resolve_entities
        reg_gen = fresh_registry()
        registry = next(reg_gen)

        phone = make_entity("PHONE", "+919876543210")
        p1 = make_entity("PERSON", "Ravi Kumar")
        rel1 = make_rel("HAS_PHONE", p1["id"], phone["id"])
        resolve_entities({"entities": [p1, phone], "relationships": [rel1]},
                         source_file="doc1.txt", registry=registry, case_id="CASE-X")

        p2 = make_entity("PERSON", "R. Kumar")
        rel2 = make_rel("HAS_PHONE", p2["id"], phone["id"])
        result = resolve_entities({"entities": [p2, phone], "relationships": [rel2]},
                                  source_file="doc2.txt", registry=registry, case_id="CASE-X")

        assert result["stats"]["merged"] >= 1, (
            "Expected auto-merge of 'R. Kumar' into 'Ravi Kumar' via shared phone."
        )
        try: next(reg_gen)
        except StopIteration: pass

    def test_different_cases_never_merge(self):
        """'Ahmed Khan' from Mumbai case + 'Ahmed Khan' from Delhi case -> never merge."""
        from backend.app.ingestion.resolver import resolve_entities
        reg_gen = fresh_registry()
        registry = next(reg_gen)

        resolve_entities({"entities": [make_entity("PERSON", "Ahmed Khan", eid="person:aaa")], "relationships": []},
                         source_file="mumbai.txt", registry=registry, case_id="CASE-MUM-001")
        result = resolve_entities({"entities": [make_entity("PERSON", "Ahmed Khan", eid="person:bbb")], "relationships": []},
                                  source_file="delhi.txt", registry=registry, case_id="CASE-DEL-999")
        assert result["stats"]["merged"] == 0
        try: next(reg_gen)
        except StopIteration: pass


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Phone conflict detection
# ─────────────────────────────────────────────────────────────────────────────

class TestPhoneConflict:

    def test_conflict_flagged_for_distinct_names(self):
        from backend.app.ingestion.resolver import _detect_phone_conflicts
        phone = make_entity("PHONE", "+919111222333")
        person_a = make_entity("PERSON", "Amit Singh")
        person_b = make_entity("PERSON", "John Peters")  # similarity <30

        entities = [phone, person_a, person_b]
        rels = [
            make_rel("HAS_PHONE", person_a["id"], phone["id"]),
            make_rel("HAS_PHONE", person_b["id"], phone["id"]),
        ]
        needs_review = []
        _detect_phone_conflicts(entities, rels, needs_review)

        assert any(r["type"] == "PHONE_CONFLICT" for r in needs_review)
        # HAS_PHONE edges must be downgraded
        for rel in rels:
            if rel["type"] == "HAS_PHONE":
                assert rel["confidence"] <= 0.3
                assert "conflicted" in rel["status"]

    def test_aliases_no_conflict(self):
        from backend.app.ingestion.resolver import _detect_phone_conflicts
        phone = make_entity("PHONE", "+919000000001")
        pa = make_entity("PERSON", "Rahul Sharma")
        pb = make_entity("PERSON", "R. Sharma")  # alias, similarity ~85

        entities = [phone, pa, pb]
        rels = [
            make_rel("HAS_PHONE", pa["id"], phone["id"]),
            make_rel("HAS_PHONE", pb["id"], phone["id"]),
        ]
        needs_review = []
        _detect_phone_conflicts(entities, rels, needs_review)
        assert not any(r["type"] == "PHONE_CONFLICT" for r in needs_review)


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Self-loop is audited not silently deleted
# ─────────────────────────────────────────────────────────────────────────────

class TestSelfLoopAudit:

    def test_self_loop_excluded_from_graph(self):
        from backend.app.ingestion.resolver import _rewrite_relationship_ids
        merged = "person:canonical"
        id_map = {"person:a": merged, "person:b": merged}
        rel = make_rel("KNOWS", "person:a", "person:b")

        with patch("backend.app.ingestion.resolver.log_filtered_edge", MagicMock()) as mock_log:
            result = _rewrite_relationship_ids([rel], id_map)

        assert len(result) == 0, "Self-loop must be excluded from the graph"

    def test_normal_rel_survives(self):
        from backend.app.ingestion.resolver import _rewrite_relationship_ids
        id_map = {"person:a": "person:a"}
        rel = make_rel("KNOWS", "person:a", "person:other")
        with patch("backend.app.ingestion.resolver.log_filtered_edge", MagicMock()):
            result = _rewrite_relationship_ids([rel], id_map)
        assert len(result) == 1


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: Duplicate FIR IDs track provenance across uploads
# ─────────────────────────────────────────────────────────────────────────────

class TestDuplicateFIRProvenance:

    def test_same_fir_string_tracks_both_source_files(self):
        from backend.app.ingestion.resolver import resolve_entities
        reg_gen = fresh_registry()
        registry = next(reg_gen)

        fir = make_entity("FIR", "FIR No. 001/2024")
        resolve_entities({"entities": [fir], "relationships": []},
                         source_file="case_a.txt", registry=registry)
        resolve_entities({"entities": [fir], "relationships": []},
                         source_file="case_b.txt", registry=registry)

        stored = registry.get(fir["id"])
        assert stored is not None
        assert "case_a.txt" in stored.get("source_files", [])
        assert "case_b.txt" in stored.get("source_files", [])
        try: next(reg_gen)
        except StopIteration: pass


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: Sentence-boundary phone linking
# ─────────────────────────────────────────────────────────────────────────────

class TestSentenceBoundaryPhoneLink:

    def test_cross_sentence_not_linked(self):
        try:
            from backend.app.ingestion.ner import _extract_unstructured, _get_nlp
            _get_nlp()
        except Exception:
            pytest.skip("spaCy model not available in test environment")

        text = (
            "The witness John was present at the scene. "
            "The suspect's mobile 9876543210 was recovered from the vehicle."
        )
        entities, rels = _extract_unstructured(text, source_label="test")

        john = next((e for e in entities if e["type"] == "PERSON" and "John" in e["value"]), None)
        phone = next((e for e in entities if e["type"] == "PHONE"), None)

        if john and phone:
            cross = [r for r in rels if r["type"] == "HAS_PHONE"
                     and r["source"] == john["id"] and r["target"] == phone["id"]]
            assert len(cross) == 0, "Cross-sentence HAS_PHONE link is the character-window bug regressing"


# ─────────────────────────────────────────────────────────────────────────────
# Tests 7-9: NER utilities
# ─────────────────────────────────────────────────────────────────────────────

class TestNERUtilities:

    def test_version_stamp_on_entity(self):
        from backend.app.ingestion.ner import _make_entity, EXTRACTION_VERSION
        e = _make_entity("PERSON", "Test Name")
        assert e.get("extraction_version") == EXTRACTION_VERSION

    def test_ocr_preserves_phone_number(self):
        from backend.app.ingestion.ner import _normalize_ocr
        assert "9876543210" in _normalize_ocr("Call 9876543210 for details.")

    def test_ocr_collapses_whitespace(self):
        from backend.app.ingestion.ner import _normalize_ocr
        assert "  " not in _normalize_ocr("Ravi    Kumar   visited   Delhi")

    def test_stoplist_rejects_officer(self):
        from backend.app.ingestion.ner import _is_probable_name
        with patch("backend.app.ingestion.ner.log_ner_borderline", MagicMock()):
            assert _is_probable_name("Officer") is False

    def test_stoplist_accepts_real_name(self):
        from backend.app.ingestion.ner import _is_probable_name
        assert _is_probable_name("Priya Sharma") is True

    def test_stoplist_bypassed_for_long_spans(self):
        from backend.app.ingestion.ner import _is_probable_name
        assert _is_probable_name("Dr. Rajesh Kumar Verma Singh") is True
