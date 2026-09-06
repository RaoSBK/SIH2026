import pytest
from ml.nlp.entity_normalization.names import normalize_name
from ml.nlp.entity_normalization.phones import normalize_phone
from ml.nlp.entity_normalization.locations import normalize_location
from ml.nlp.entity_normalization.identifiers import normalize_identifier
from ml.nlp.ner.inference import predict_entities

def test_normalize_name():
    assert normalize_name("Mr. Ravi Kumar!") == "Ravi Kumar"
    assert normalize_name("Shri Advocate Suresh Sharma") == "Suresh Sharma"
    assert normalize_name("john doe") == "John Doe"

def test_normalize_phone():
    assert normalize_phone("+91-98765 43210") == "9876543210"
    assert normalize_phone("09876543210") == "9876543210"
    assert normalize_phone("9876543210") == "9876543210"

def test_normalize_location():
    assert normalize_location("Andheri P.S.") == "Andheri Police Station"
    assert normalize_location("MG Rd. Section 4") == "MG Road Section 4"

def test_normalize_identifier():
    assert normalize_identifier("mh-12 ab 1234", "VEHICLE") == "MH12AB1234"
    assert normalize_identifier("case 102", "CASE_ID") == "CASE-102"

def test_predict_entities():
    text = "Suspect Mr. Ravi Kumar was seen at Andheri P.S. with phone +91-9876543210 and vehicle MH-12-AB-1234."
    entities = predict_entities(text)
    assert isinstance(entities, list)
    assert len(entities) >= 1
    # Check normalized value exists
    for ent in entities:
        assert "normalized_value" in ent
