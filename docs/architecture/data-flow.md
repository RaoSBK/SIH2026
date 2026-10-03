# End-to-End Data Flow & 7-Stage Pipeline

This document details the data lifecycle as unstructured case evidence flows through the 7-stage VERITAS processing engine into the interactive investigator console.

Source Code: [`backend/app/api/ingestion.py`](file:///d:/SIH2026/backend/app/api/ingestion.py#L65-L270), [`backend/app/ingestion/service.py`](file:///d:/SIH2026/backend/app/ingestion/service.py)

```
 ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
 │ 1. INGEST │───►│2.NORMALIZE│───►│ 3. EXTRACT│───►│4. RESOLVE │
 └───────────┘    └───────────┘    └───────────┘    └───────────┘
                                                          │
 ┌───────────┐    ┌───────────┐    ┌───────────┐          │
 │7. EXPLAIN │◄───│6. ANALYZE │◄───│  5. GRAPH │◄─────────┘
 └───────────┘    └───────────┘    └───────────┘
```

## Stage-by-Stage Flow Breakdown

### Stage 0: Ingest
- **Trigger**: Investigator uploads files via `POST /api/process-evidence`.
- **Actions**:
  - File binary is read, SHA-256 digest calculated, and recorded in the cryptographic evidence ledger (`evidence_ledger.json`).
  - Metadata is saved to PostgreSQL `evidence` table.
  - File is dispatched to format parser (`pdf_parser.py`, `docx_parser.py`, `csv_parser.py`, `json_parser.py`, `txt_parser.py`).

### Stage 1: Normalize
- **Actions**:
  - Phone numbers converted to standard E.164 format (`+91XXXXXXXXXX`).
  - Names cleaned of honorifics, titles, and extra whitespace.
  - Bank account strings and vehicle registration numbers standardized.

### Stage 2: Extract (Multilingual NER & Pattern Matching)
- **Actions**:
  - Parallel execution via `asyncio.gather()` / `asyncio.to_thread()`.
  - spaCy `en_core_web_sm` model extracts `PERSON`, `LOCATION`, `ORG` entities.
  - Custom regex engines extract `PHONE`, `VEHICLE`, `ACCOUNT`, `FIR`, `AADHAAR` entities.
  - Sentence co-occurrence and verb trigger rules extract directed relationship triples.

### Stage 3: Resolve (Multi-Signal Disambiguation)
- **Actions**:
  - Candidates compared using Double Metaphone phonetics and Jaro-Winkler distance (`cias_er`).
  - High confidence ($\ge 0.85$) items merged automatically.
  - Medium confidence ($0.65 - 0.85$) items appended to `/api/review-queue`.
  - Phone attribute propagation merges co-occurring Person-Phone pairs.

### Stage 4: Graph (Batched Neo4j Persistence)
- **Actions**:
  - High-performance Cypher queries (`UNWIND` batches) insert nodes and relationships into Neo4j.
  - Provenance links (`:EXTRACTED_FROM`) connect every node to its parent `Document` node.

### Stage 5: Analyze (Anomaly Detection & Network Analytics)
- **Actions**:
  - Rule engine checks degree thresholds ($\ge 5$ connections) and structuring patterns.
  - Isolation Forest ML model flags structural graph outliers.
  - NetworkX computes PageRank (kingpins) and Betweenness (bridges).

### Stage 6: Explain (Indicator Attachment)
- **Actions**:
  - Node risk colors (`red`, `orange`, `none`) assigned.
  - Detailed evidence trails and anomaly justification strings attached to node metadata.

### Stage 7: Complete
- **Actions**:
  - WebSocket pushes completion status to investigator UI console.
  - Interactive D3.js force-directed graph renders full case network.
