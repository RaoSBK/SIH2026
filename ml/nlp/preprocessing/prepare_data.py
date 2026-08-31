import os
import json
import spacy
from spacy.tokens import DocBin
import logging

logging.basicConfig(level=logging.INFO)

def create_spacy_dataset(json_file_path, output_path):
    nlp = spacy.blank("en")
    db = DocBin()
    
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    logging.info(f"Loaded {len(data)} records from {json_file_path}")
    
    skipped = 0
    for record in data:
        text = record['text']
        entities = record['entities']
        
        doc = nlp.make_doc(text)
        ents = []
        for start, end, label in entities:
            span = doc.char_span(start, end, label=label, alignment_mode="contract")
            if span is None:
                # This happens if the character offsets don't align with token boundaries.
                logging.warning(f"Skipping entity {label} in text: '{text[start:end]}'")
            else:
                ents.append(span)
                
        # Filter out overlapping entities (just in case)
        filtered_ents = spacy.util.filter_spans(ents)
        doc.ents = filtered_ents
        db.add(doc)
        
    db.to_disk(output_path)
    logging.info(f"Saved .spacy dataset to {output_path}. Skipped misaligned spans: {skipped}")

def main():
    input_dir = "data/synthetic/training"
    output_dir = "data/synthetic/training/spacy"
    os.makedirs(output_dir, exist_ok=True)
    
    train_json = os.path.join(input_dir, "train.json")
    dev_json = os.path.join(input_dir, "dev.json")
    
    train_spacy = os.path.join(output_dir, "train.spacy")
    dev_spacy = os.path.join(output_dir, "dev.spacy")
    
    create_spacy_dataset(train_json, train_spacy)
    create_spacy_dataset(dev_json, dev_spacy)

if __name__ == "__main__":
    main()
