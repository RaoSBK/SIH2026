import pytest
from ml.nlp.ner.inference import predict_entities

def test_predict_entities_person():
    text = "Suspect John Doe was spotted at the bank."
    entities = predict_entities(text)
    assert isinstance(entities, list)
    types = [e["type"] for e in entities]
    assert "PERSON" in types

def test_predict_entities_phone_vehicle():
    text = "Contact 9876543210 drove vehicle MH12AB1234."
    entities = predict_entities(text)
    types = [e["type"] for e in entities]
    assert "PHONE" in types or "VEHICLE" in types
