"""
Test for resolver.py (Task 4).
Run from project root: python -X utf8 backend/tests/test_resolver.py
"""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Use a temporary registry so tests don't pollute production data
import tempfile, json
from app.ingestion.resolver import EntityRegistry, resolve_entities

def make_registry():
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w', encoding='utf-8')
    json.dump({"entities": {}}, tmp)
    tmp.close()
    return EntityRegistry(registry_path=tmp.name)

def print_section(title):
    print(f"\n{'='*60}\n{title}\n{'='*60}")

# ── Helpers to build fake ner.py output ──────────────────────────────────────
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


# ════════════════════════════════════════════════════════════
# TEST 1: Phone exact dedup across two files
# ════════════════════════════════════════════════════════════
print_section("TEST 1: Phone exact dedup across two files")

reg = make_registry()
p1 = phone_entity("+919876543210")
p2 = phone_entity("+919876543210")  # same number, different file

result1 = resolve_entities({"entities": [p1], "relationships": []},
                            source_file="file_A.csv", registry=reg)
result2 = resolve_entities({"entities": [p2], "relationships": []},
                            source_file="file_B.csv", registry=reg)

stored = reg.get(p1["id"])
print(f"Same phone from 2 files -> source_files: {stored['source_files']}")
print(f"File A stats: {result1['stats']}")
print(f"File B stats: {result2['stats']}  (should be 0 new, 1 merged/enriched)")
assert stored and "file_B.csv" in stored["source_files"], "FAIL: provenance not merged"
print("PASS")


# ════════════════════════════════════════════════════════════
# TEST 2: Person name fuzzy — auto-merge (>= 90%)
# ════════════════════════════════════════════════════════════
print_section("TEST 2: Person auto-merge (similarity >= 90%)")

reg = make_registry()
p_known  = person_entity("Ravi Kumar")
p_typo   = person_entity("Ravi Kumara")  # one char suffix — should auto-merge

result1 = resolve_entities({"entities": [p_known], "relationships": []},
                            source_file="fir_001.txt", registry=reg)
result2 = resolve_entities({"entities": [p_typo],  "relationships": []},
                            source_file="fir_002.txt", registry=reg)

print(f"File 1 stats: {result1['stats']}")
print(f"File 2 stats: {result2['stats']}")
print(f"needs_review in file 2: {len(result2['needs_review'])}  (should be 0)")
canonical = result2["resolved_entities"][0] if result2["resolved_entities"] else None
if canonical:
    print(f"Canonical name: '{canonical['value']}', aliases: {canonical.get('aliases')}")
print("PASS" if result2["stats"]["merged"] >= 1 else "FAIL: auto-merge did not fire")


# ════════════════════════════════════════════════════════════
# TEST 3: Person name fuzzy — flag for review (70-89%)
# ════════════════════════════════════════════════════════════
print_section("TEST 3: Person flagged for review (70-89% similarity)")

reg = make_registry()
# "Ravi Kumar Singh" vs "Ravi Kumar Sharma" — same first+last, different family name
# token_sort_ratio ≈ 80% — in the review zone, not auto-merge
p_a = person_entity("Ravi Kumar Singh")
p_b = person_entity("Ravi Kumar Sharma")

result1 = resolve_entities({"entities": [p_a], "relationships": []},
                            source_file="surv_001.txt", registry=reg)
result2 = resolve_entities({"entities": [p_b], "relationships": []},
                            source_file="surv_002.txt", registry=reg)

nr = result2["needs_review"]
print(f"needs_review count: {len(nr)}  (should be > 0)")
if nr:
    item = nr[0]
    print(f"  candidate: '{item['candidate']['value']}'")
    print(f"  possible_match: '{item['possible_match']['value']}'")
    print(f"  similarity: {item['similarity']}")
    print(f"  reason: {item['reason']}")
print("PASS" if len(nr) > 0 else "FAIL: should have been flagged")


# ════════════════════════════════════════════════════════════
# TEST 4: Location normalization + merge
# ════════════════════════════════════════════════════════════
print_section("TEST 4: Location normalization (M.G. Road vs MG Road)")

reg = make_registry()
loc_a = location_entity("M.G. Road, Bangalore")
loc_b = location_entity("MG Road Bangalore")

result1 = resolve_entities({"entities": [loc_a], "relationships": []},
                            source_file="fir_loc_001.txt", registry=reg)
result2 = resolve_entities({"entities": [loc_b], "relationships": []},
                            source_file="fir_loc_002.txt", registry=reg)

print(f"File 1 stats: {result1['stats']}")
print(f"File 2 stats: {result2['stats']}")
merged = result2["stats"]["merged"]
print(f"Locations merged: {merged}  (should be 1)")
print("PASS" if merged >= 1 else "FAIL: location merge did not fire")


# ════════════════════════════════════════════════════════════
# TEST 5: Relationship pointer rewriting after merge
# ════════════════════════════════════════════════════════════
print_section("TEST 5: Relationship pointers rewritten after person merge")

reg = make_registry()
p_orig  = person_entity("Amit Singh")
p_typo  = person_entity("Amit Sing")    # should auto-merge into p_orig
phone   = phone_entity("+919000000001")
rel     = make_rel("HAS_PHONE", p_typo["id"], phone["id"], confidence=0.5)

result1 = resolve_entities({"entities": [p_orig], "relationships": []},
                            source_file="doc1.txt", registry=reg)
result2 = resolve_entities({"entities": [p_typo, phone], "relationships": [rel]},
                            source_file="doc2.txt", registry=reg)

rewritten_rels = result2["resolved_relationships"]
print(f"Original relationship source: {p_typo['id']}")
for r in rewritten_rels:
    print(f"  Rewritten source: {r['source']}  (should match canonical: {p_orig['id']})")
print("PASS" if all(r["source"] != p_typo["id"] for r in rewritten_rels) else
      "FAIL: stale ID not rewritten")
