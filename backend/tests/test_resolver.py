"""
Test for resolver.py (Task 4).
Run from project root: python -X utf8 backend/tests/test_resolver.py
"""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Use a temporary registry so tests don't pollute production data
import tempfile, json
from app.ingestion.resolver import EntityRegistry, resolve_entities

def make_registry():
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w', encoding='utf-8')
    json.dump({"entities": {}}, tmp)
    tmp.close()
    return EntityRegistry(registry_path=tmp.name)

def phone_entity(number):
    import hashlib
    eid = f"phone:{hashlib.sha256(number.encode()).hexdigest()[:8]}"
    return {"id": eid, "type": "PHONE", "value": number, "confidence": 1.0, "attributes": {}}

def person_entity(name):
    import hashlib
    eid = f"person:{hashlib.sha256(name.encode()).hexdigest()[:8]}"
    return {"id": eid, "type": "PERSON", "value": name, "confidence": 0.85, "attributes": {}}

def location_entity(loc):
    import hashlib
    eid = f"location:{hashlib.sha256(loc.encode()).hexdigest()[:8]}"
    return {"id": eid, "type": "LOCATION", "value": loc, "confidence": 0.85, "attributes": {}}

def make_rel(rtype, source_id, target_id, confidence=1.0):
    import uuid
    return {"id": str(uuid.uuid4()), "type": rtype, "source": source_id,
            "target": target_id, "confidence": confidence, "status": "confirmed",
            "evidence": "test", "attributes": {}}


def test_phone_dedup():
    reg = make_registry()
    p1 = phone_entity("+919876543210")
    p2 = phone_entity("+919876543210")

    result1 = resolve_entities({"entities": [p1], "relationships": []},
                                source_file="file_A.csv", registry=reg)
    result2 = resolve_entities({"entities": [p2], "relationships": []},
                                source_file="file_B.csv", registry=reg)

    stored = reg.get(p1["id"])
    assert stored and "file_B.csv" in stored["source_files"], "FAIL: provenance not merged"

def test_person_automerge():
    reg = make_registry()
    p_known  = person_entity("Ravi Kumar")
    p_typo   = person_entity("Ravi Kumara")

    result1 = resolve_entities({"entities": [p_known], "relationships": []},
                                source_file="fir_001.txt", registry=reg, case_id="CASE-001")
    result2 = resolve_entities({"entities": [p_typo],  "relationships": []},
                                source_file="fir_002.txt", registry=reg, case_id="CASE-001")

    assert result2["stats"]["merged"] >= 1, "FAIL: auto-merge did not fire"

def test_person_flagged():
    reg = make_registry()
    p_a = person_entity("Ravi Kumar Singh")
    p_b = person_entity("Ravi Kumar Sharma")

    result1 = resolve_entities({"entities": [p_a], "relationships": []},
                                source_file="surv_001.txt", registry=reg)
    result2 = resolve_entities({"entities": [p_b], "relationships": []},
                                source_file="surv_002.txt", registry=reg)

    nr = result2["needs_review"]
    assert len(nr) > 0, "FAIL: should have been flagged"

def test_location_normalization():
    reg = make_registry()
    loc_a = location_entity("M.G. Road, Bangalore")
    loc_b = location_entity("MG Road Bangalore")

    result1 = resolve_entities({"entities": [loc_a], "relationships": []},
                                source_file="fir_loc_001.txt", registry=reg)
    result2 = resolve_entities({"entities": [loc_b], "relationships": []},
                                source_file="fir_loc_002.txt", registry=reg)

    merged = result2["stats"]["merged"]
    assert merged >= 1, "FAIL: location merge did not fire"

def test_relationship_rewriting():
    reg = make_registry()
    p_orig  = person_entity("Amit Singh")
    p_typo  = person_entity("Amit Sing")
    phone   = phone_entity("+919000000001")
    rel     = make_rel("HAS_PHONE", p_typo["id"], phone["id"], confidence=0.5)

    result1 = resolve_entities({"entities": [p_orig], "relationships": []},
                                source_file="doc1.txt", registry=reg, case_id="CASE-002")
    result2 = resolve_entities({"entities": [p_typo, phone], "relationships": [rel]},
                                source_file="doc2.txt", registry=reg, case_id="CASE-002")

    rewritten_rels = result2["resolved_relationships"]
    assert all(r["source"] != p_typo["id"] for r in rewritten_rels), "FAIL: stale ID not rewritten"
