"""
Quick verification test for ner.py (Task 3).
Run from project root: python backend/tests/test_ner.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.ingestion.parsers.csv_parser import parse_csv
from app.ingestion.ner import extract_entities
import json

# ── Test 1: Structured Path ───────────────────────────────────────────────────
print("=" * 60)
print("TEST 1: Structured Path (mock_cdr.csv)")
print("=" * 60)
parsed = parse_csv("data/mock_cdr.csv")
result = extract_entities(parsed)
print(f"Entities  : {len(result['entities'])}")
print(f"Relations : {len(result['relationships'])}")
for r in result["relationships"]:
    print(f"  [{r['confidence']}] {r['type']} | {r['status']} | {r['evidence']}")

# ── Test 2: Unstructured Path (Mock FIR Text) ─────────────────────────────────
print()
print("=" * 60)
print("TEST 2: Unstructured Path (Mock FIR Text)")
print("=" * 60)
mock_fir = """
FIR No. 145/2026
On 29-Aug-2026, accused Ravi Kumar met Farhan Sheikh at Andheri Station.
Ravi Kumar called 9876543210 and transferred funds to suspect.
The vehicle MH-12-AB-1234 was found near the scene.
Farhan Sheikh was seen using phone 9123456789.
Aadhaar details collected: 1234 5678 9012 (suspect identity confirmed).
"""
parsed_fir = {
    "data_shape": "unstructured",
    "content": mock_fir,
    "detected_subtype": "fir",
    "warnings": []
}
result2 = extract_entities(parsed_fir, source_label="test")
print(f"Entities  : {len(result2['entities'])}")
for e in result2["entities"]:
    print(f"  [{e['confidence']}] {e['type']:12s} | {e['value']}")

print(f"\nRelationships: {len(result2['relationships'])}")
for r in result2["relationships"]:
    print(f"  [{r['confidence']}] {r['type']:20s} | {r['status']}")
    print(f"    Evidence: {r['evidence'][:80]}...")
