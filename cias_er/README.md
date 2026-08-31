# CIAS Entity Resolution Module

This module takes extracted entities from NLP/NER modules and clusters them into distinct, real-world identities to be used as nodes in the CIAS Knowledge Graph.

## Key Features
1. **Fuzzy Name Matching**: Uses RapidFuzz (Jaro-Winkler similarity) to catch typos and abbreviations (e.g., "Ravi Kumar" vs "R. Kumar").
2. **Identifier Weighting**: Exact or partial phone number matches strongly bind identities.
3. **Graph-Based Resolution**: Forms components where nodes are entities and edges are confidence scores above `0.5`.
4. **Historical Profiling**: Simulates FIR lookups against a criminal database, tagging clusters with a `risk_color` (yellow, orange, red).

## Graph UI Integration
The output provides `links` with a `line_type` parameter:
- **`solid`** (`confidence >= 0.85`): High confidence match.
- **`dotted`** (`confidence < 0.85`): Ambiguous match. The UI should render this as a dotted line. Any cluster containing a dotted link is flagged with `"status": "REVIEW_REQUIRED"`.

## Usage
```python
from cias_er import resolve_entities

input_data = [
    {
        "id": "E1",
        "name": "Don Dawood",
        "phone": "9998887777"
    }
]

result = resolve_entities(input_data)
# result['nodes'] -> Contains nodes enriched with historical_firs and risk_color
# result['links'] -> Contains the edges with line_type (solid/dotted)
```
