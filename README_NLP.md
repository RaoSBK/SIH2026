# CIAS NLP and Relation Extraction Module

This module is responsible for Named Entity Recognition (NER) and Relation Extraction on unstructured CIAS text sources (like FIRs, surveillance logs, and intelligence notes).

## Architecture

The module uses a hybrid approach based on the `spaCy` library:
1. **Statistical NER**: Uses `en_core_web_sm` to identify standard entities like `PERSON`, `ORG`, `LOCATION`, and `DATE`. It's particularly useful for picking out varying names in natural language contexts.
2. **Rule-based (Regex/Patterns)**: Uses spaCy's `EntityRuler` to enforce rigid extraction for specific formats such as `PHONE` (10 digits), `VEHICLE` (e.g., MH12AB1234), and `CASE_ID`.
3. **Relation Extraction**: A lightweight, heuristic-based logic that looks for co-occurrences of entities within the same sentence to define relationships (`USES`, `VISITED`, `ASSOCIATED_WITH`, `IN_CONTACT_WITH`).

## Setup

1. **Install Dependencies**:
```bash
pip install spacy
python -m spacy download en_core_web_sm
```

## Usage

You can use the `process_text` function to process a document string:

```python
import json
from scripts.cias_nlp import process_text

text = "Case ID: CASE-004. Subject Ravi Kumar was identified near Location_12. Contact number 9123456780 was found. A vehicle bearing plate MH12PQ5678 was noted."

output = process_text(text, document_id="FIR-001")
print(json.dumps(output, indent=2))
```

## Output Format

The output is a strict, structured JSON:
```json
{
  "document_id": "FIR-001",
  "entities": [
    {
      "id": "E1",
      "text": "CASE-004",
      "type": "CASE_ID",
      "span": [
        9,
        17
      ]
    }
  ],
  "relations": [
    {
      "subject": "E2",
      "predicate": "VISITED",
      "object": "E3",
      "confidence": 0.7
    }
  ]
}
```

## Validation

To run tests on the synthetic data in this repository, execute:
```bash
python scripts/test_nlp.py
```
This script reads samples from the `data/fir`, `data/surveillance`, and `data/intelligence` directories, prints the results, and dumps a full `nlp_test_output.json` to the root folder.
