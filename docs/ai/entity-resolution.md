# Multi-Signal Entity Resolution & Disambiguation

Entity Resolution (ER) merges duplicate mentions of the same real-world entity across disparate evidence files while routing ambiguous candidate matches to human investigators.

## Implementation Architecture

Source Code: [`backend/app/ingestion/resolver.py`](file:///d:/SIH2026/backend/app/ingestion/resolver.py), [`cias_er/`](file:///d:/SIH2026/cias_er/)

```mermaid
flowchart TD
    Raw["Raw Extracted Entities (NER / RegEx)"] --> Norm["Standardize & Normalize (E.164 Phones, Case, Account Format)"]
    Norm --> Match["Multi-Signal Candidate Matching (cias_er)"]
    
    Match --> PhoneCheck{"Exact Phone Match?"}
    PhoneCheck -- Yes --> AutoMerge["Automatic Entity Node Merge (Neo4j)"]
    
    PhoneCheck -- No --> ScoreCheck{"Calculate Jaro-Winkler & Double Metaphone Score"}
    ScoreCheck -- "Score >= 0.85" --> AutoMerge
    ScoreCheck -- "0.65 <= Score < 0.85" --> ReviewQueue["Queue to /api/review-queue (Human Review)"]
    ScoreCheck -- "Score < 0.65" --> KeepDistinct["Keep as Distinct Entities"]
    
    ReviewQueue --> InvestigatorDecision{"Investigator Choice"}
    InvestigatorDecision -- "action: 'merge'" --> AutoMerge
    InvestigatorDecision -- "action: 'reject'" --> KeepDistinct

    style AutoMerge fill:#99ff99,stroke:#009900,stroke-width:1.5px
    style ReviewQueue fill:#ffff99,stroke:#cc9900,stroke-width:1.5px
    style KeepDistinct fill:#e0e0e0,stroke:#666666,stroke-width:1px
```


## Resolution Signals & Scoring

1. **Phone Standardization**: All phone numbers are converted to normalized E.164 strings (`+91XXXXXXXXXX`). Matching phones across different FIRs or CDRs are merged automatically.
2. **Phonetic Encoding**: Names are encoded using Double Metaphone and Soundex via `cias_er/matcher.py`. This resolves phonetic misspellings across police stations (e.g., "Faisal Khan" vs. "Faizal Cahn").
3. **Fuzzy String Distance**: Jaro-Winkler distance is computed across candidate name strings using `RapidFuzz`.
4. **Case-Scoped Isolation**: Candidate comparisons are filtered by `case_id` to prevent inadvertent cross-case merging unless cross-case analysis is explicitly invoked.

## Human-in-the-Loop Review Queue

Ambiguous identity matches (e.g., phonetic similarity score between 0.65 and 0.85) are not merged automatically. Instead:
- Items are appended to `needs_review` inside `data/entity_registry.json`.
- Investigators view these items via `GET /api/review-queue`.
- Resolving an item via `POST /api/review-queue/{review_id}/resolve` with action `"merge"` triggers an automated Cypher node merge in Neo4j (`merge_nodes_in_neo4j`).
