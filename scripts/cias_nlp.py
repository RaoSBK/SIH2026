import spacy
from spacy.pipeline import EntityRuler
import json
import uuid

# Global spaCy model instance
_nlp = None

def get_nlp_pipeline():
    """Lazy load and configure the spaCy pipeline."""
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading language model for the first time...")
            from spacy.cli import download
            download("en_core_web_sm")
            _nlp = spacy.load("en_core_web_sm")

        # Add rule-based entity matching for specific structures
        ruler = _nlp.add_pipe("entity_ruler", before="ner")
        
        patterns = [
            # Phone number pattern (10 digits)
            {"label": "PHONE", "pattern": [{"TEXT": {"REGEX": r"\b\d{10}\b"}}]},
            # Vehicle plate pattern (e.g., MH12AB1234)
            {"label": "VEHICLE", "pattern": [{"TEXT": {"REGEX": r"\b[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{4}\b"}}]},
            # Case ID pattern (e.g., CASE-123)
            {"label": "CASE_ID", "pattern": [{"TEXT": {"REGEX": r"\bCASE-\d{3}\b"}}]}
        ]
        ruler.add_patterns(patterns)
    
    return _nlp

def extract_entities(doc):
    """Extract entities and assign them stable IDs."""
    entities = []
    ent_mapping = {} # mapping from (start_char, end_char) to entity ID
    
    for i, ent in enumerate(doc.ents):
        # Filter and normalize standard spaCy labels
        label = ent.label_
        if label in ["PERSON", "ORG", "GPE", "LOC", "DATE", "PHONE", "VEHICLE", "CASE_ID"]:
            # Normalize GPE/LOC to LOCATION
            if label in ["GPE", "LOC"]:
                label = "LOCATION"
            
            ent_id = f"E{i+1}"
            entities.append({
                "id": ent_id,
                "text": ent.text,
                "type": label,
                "span": [ent.start_char, ent.end_char]
            })
            ent_mapping[(ent.start_char, ent.end_char)] = ent_id
            
    return entities, ent_mapping

def extract_relations(doc, entities_data, ent_mapping):
    """
    Extract relationships between entities using simple co-occurrence within sentences
    and simple dependency-based heuristics.
    """
    relations = []
    
    # Pre-process entities by span for easy lookup
    span_to_entity = {span: ent for span, ent in ent_mapping.items()}
    
    # We will look at each sentence to find relations
    for sent in doc.sents:
        sent_entities = []
        for ent in sent.ents:
            span = (ent.start_char, ent.end_char)
            if span in span_to_entity:
                sent_entities.append({
                    "id": span_to_entity[span],
                    "type": ent.label_ if ent.label_ not in ["GPE", "LOC"] else "LOCATION",
                    "text": ent.text,
                    "span": span
                })
        
        # Simple relation rules within the same sentence
        for i in range(len(sent_entities)):
            for j in range(i + 1, len(sent_entities)):
                ent1 = sent_entities[i]
                ent2 = sent_entities[j]
                
                # Rule 1: PERSON in contact with / uses PHONE
                if (ent1["type"] == "PERSON" and ent2["type"] == "PHONE") or \
                   (ent2["type"] == "PERSON" and ent1["type"] == "PHONE"):
                    p_id = ent1["id"] if ent1["type"] == "PERSON" else ent2["id"]
                    ph_id = ent1["id"] if ent1["type"] == "PHONE" else ent2["id"]
                    
                    relations.append({
                        "subject": p_id,
                        "predicate": "USES",
                        "object": ph_id,
                        "confidence": 0.8 # Co-occurrence heuristic
                    })
                
                # Rule 2: PERSON visited / near LOCATION
                elif (ent1["type"] == "PERSON" and ent2["type"] == "LOCATION") or \
                     (ent2["type"] == "PERSON" and ent1["type"] == "LOCATION"):
                    p_id = ent1["id"] if ent1["type"] == "PERSON" else ent2["id"]
                    loc_id = ent1["id"] if ent1["type"] == "LOCATION" else ent2["id"]
                    
                    relations.append({
                        "subject": p_id,
                        "predicate": "VISITED",
                        "object": loc_id,
                        "confidence": 0.7
                    })
                    
                # Rule 3: PERSON associated with ORG
                elif (ent1["type"] == "PERSON" and ent2["type"] == "ORG") or \
                     (ent2["type"] == "PERSON" and ent1["type"] == "ORG"):
                    p_id = ent1["id"] if ent1["type"] == "PERSON" else ent2["id"]
                    org_id = ent1["id"] if ent1["type"] == "ORG" else ent2["id"]
                    
                    relations.append({
                        "subject": p_id,
                        "predicate": "ASSOCIATED_WITH",
                        "object": org_id,
                        "confidence": 0.7
                    })
                    
                # Rule 4: PERSON in contact with PERSON
                elif ent1["type"] == "PERSON" and ent2["type"] == "PERSON":
                    sent_text = sent.text.lower()
                    if "contact" in sent_text or "observed" in sent_text or "with" in sent_text:
                        relations.append({
                            "subject": ent1["id"],
                            "predicate": "IN_CONTACT_WITH",
                            "object": ent2["id"],
                            "confidence": 0.6
                        })
                        
    return relations

def process_text(text, document_id=None):
    """
    Main function to process unstructured text and return structured JSON.
    """
    if not document_id:
        document_id = str(uuid.uuid4())
        
    nlp = get_nlp_pipeline()
    doc = nlp(text)
    
    entities, ent_mapping = extract_entities(doc)
    relations = extract_relations(doc, entities, ent_mapping)
    
    output = {
        "document_id": document_id,
        "entities": entities,
        "relations": relations
    }
    
    return output

if __name__ == "__main__":
    # Small test
    sample_text = "Case ID: CASE-004. Subject Ravi Kumar was identified near Location_12. Contact number 9123456780 was found. A vehicle bearing plate MH12PQ5678 was noted."
    result = process_text(sample_text, document_id="TEST-01")
    print(json.dumps(result, indent=2))
