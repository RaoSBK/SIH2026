# Natural Language Processing (NLP) & Entity Extraction

The VERITAS NLP module extracts criminal entities and relationship triples from unstructured case documents (FIRs, interrogation summaries, surveillance transcripts, CDRs, and banking ledgers).

## Pipeline Implementation

Source Code: [`backend/app/ingestion/ner.py`](file:///d:/SIH2026/backend/app/ingestion/ner.py), [`backend/app/ingestion/relevance.py`](file:///d:/SIH2026/backend/app/ingestion/relevance.py)

### 1. Domain Relevance Gating
Before entity extraction begins, documents are evaluated against criminal intelligence keyword patterns in `relevance.py`. Non-relevant files are flagged or filtered early to prevent noise in the knowledge graph.

### 2. Extracted Entity Types

| Entity Type | Extraction Technique | Example Pattern / Target | Source Handler |
|---|---|---|---|
| **`PERSON`** | spaCy NER (`en_core_web_sm`) + Regex | Name strings (e.g., "Faisal Khan", "Vikram Sharma") | `extract_entities()` |
| **`PHONE`** | E.164 Standardized Regex | International & Indian phone formats (e.g., `+919876543210`) | `extract_phone_numbers()` |
| **`VEHICLE`** | State Code & Registration Regex | Vehicle registration plates (e.g., `MH-12-AB-1234`, `DL-01-C-9876`) | `extract_vehicle_numbers()` |
| **`LOCATION`** | spaCy `GPE`/`LOC` + Gazetteers | Cities, neighborhoods, landmark locations | `extract_entities()` |
| **`ACCOUNT`** | Financial Account Regex | Bank account numbers & UPI IDs (e.g., `ACC-AHMED-4521`) | `extract_account_numbers()` |
| **`ORG`** | spaCy `ORG` + Regex | Business fronts, shell companies, organizations | `extract_entities()` |
| **`FIR`** | Reference ID Regex | FIR registration codes (e.g., `FIR-2024-0089`) | `extract_fir_references()` |
| **`AADHAAR`** | 12-Digit Verhoeff Regex | Masked Aadhaar numbers with SHA-256 hash | `extract_aadhaar_numbers()` |

### 3. Relationship Extraction Rules

Relationships are extracted via co-occurrence sliding windows and verb trigger analysis:
- **`CALLED`**: Extracted directly from Call Data Record (CDR) CSV/JSON records with duration, timestamp, and tower location.
- **`TRANSFERRED_TO`**: Extracted from banking transaction records with amount, timestamp, and transaction ID.
- **`HAS_PHONE`**: Link formed when a `PERSON` and `PHONE` co-occur in the same sentence or paragraph context.
- **`OWNS_VEHICLE`**: Link formed when a `PERSON` and `VEHICLE` registration appear in close textual proximity.
- **`ASSOCIATED_WITH`**: Link formed between `PERSON` and `ORG` or between co-named suspects.
- **`<VERB_TRIGGER>`**: Dynamic upper-case relationships generated from sentence dependency trees (e.g., `MET`, `OPERATES`, `PAID`, `THREATENED`).

## Extracted Provenance & Evidence Trail

Every extracted entity node and relationship edge stores a list of `source_files` and `evidence_trail` snippets. This provides 100% traceability back to original FIR pages or CDR rows.
