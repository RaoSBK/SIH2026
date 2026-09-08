"""
Quick verification test for ner.py (Task 3).
Run from project root: python backend/tests/test_ner.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.ingestion.parsers.csv_parser import parse_csv
from app.ingestion.ner import extract_entities
import json

def test_ner_structured_path():
    parsed = parse_csv("data/mock_cdr.csv")
    result = extract_entities(parsed)
    assert len(result['entities']) > 0
    assert len(result['relationships']) > 0

def test_ner_unstructured_path():
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
    assert len(result2['entities']) > 0
    assert len(result2['relationships']) > 0
