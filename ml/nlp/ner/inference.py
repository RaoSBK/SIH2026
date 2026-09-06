from typing import List, Dict, Any
from .model import NERModelManager
from ..entity_normalization.names import normalize_name
from ..entity_normalization.phones import normalize_phone
from ..entity_normalization.locations import normalize_location
from ..entity_normalization.identifiers import normalize_identifier

def predict_entities(text: str) -> List[Dict[str, Any]]:
    """
    Runs spaCy NER inference on text and applies normalization submodules.
    
    Returns:
        list: [{"id": "E1", "text": "Ravi Kumar", "normalized_value": "Ravi Kumar", "type": "PERSON", "span": [10, 20]}, ...]
    """
    if not text:
        return []

    nlp = NERModelManager.get_nlp()
    doc = nlp(text)

    entities = []
    for i, ent in enumerate(doc.ents):
        label = ent.label_
        raw_val = ent.text.strip()

        if label in ("GPE", "LOC"):
            norm_type = "LOCATION"
            norm_val = normalize_location(raw_val)
        elif label == "PERSON":
            norm_type = "PERSON"
            norm_val = normalize_name(raw_val)
        elif label == "PHONE":
            norm_type = "PHONE"
            norm_val = normalize_phone(raw_val)
        elif label in ("VEHICLE", "PLATE"):
            norm_type = "VEHICLE"
            norm_val = normalize_identifier(raw_val, "VEHICLE")
        elif label == "CASE_ID":
            norm_type = "CASE_ID"
            norm_val = normalize_identifier(raw_val, "CASE_ID")
        elif label in ("ORG", "ORGANIZATION"):
            norm_type = "ORGANIZATION"
            norm_val = raw_val
        else:
            norm_type = label
            norm_val = raw_val

        entities.append({
            "id": f"E{i+1}",
            "text": raw_val,
            "normalized_value": norm_val,
            "type": norm_type,
            "span": [ent.start_char, ent.end_char]
        })

    return entities
