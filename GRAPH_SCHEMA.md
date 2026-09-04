# GRAPH_SCHEMA.md

Last verified: 2026-09-04
Source of truth for every item below: [`backend/app/database/neo4j.py`](file:///d:/SIH2026/backend/app/database/neo4j.py), [`backend/app/main.py`](file:///d:/SIH2026/backend/app/main.py), [`backend/app/ingestion/ner.py`](file:///d:/SIH2026/backend/app/ingestion/ner.py), [`backend/app/ingestion/resolver.py`](file:///d:/SIH2026/backend/app/ingestion/resolver.py), [`graph/generate_anomaly_data.py`](file:///d:/SIH2026/graph/generate_anomaly_data.py)

---

## Node labels currently produced by the live pipeline

All entity nodes created during ingestion are merged on property `id` via [`backend/app/database/neo4j.py:L26-L39`](file:///d:/SIH2026/backend/app/database/neo4j.py#L26-L39).

### 1. `Document`
- **Primary Key / Merge Query**: `file_name`, `case_id`
- **Properties**:
  - `file_name` (string): Originating document filename (e.g. `FIR_001_Faisal_Khan.pdf`)
  - `case_id` (string): Associated case identifier (e.g. `CASE-102`)
- **Created in**: [`backend/app/database/neo4j.py:L19-L23`](file:///d:/SIH2026/backend/app/database/neo4j.py#L19-L23)

### 2. `PERSON`
- **Primary Key / Merge Query**: `id` (e.g. `person:a7ca11a0`)
- **Properties**:
  - `id` (string): Unique node identifier
  - `value` (string): Canonical name string (e.g. `Faisal Khan`)
  - `type` (string): `"PERSON"`
  - `confidence` (float): Extraction confidence score (`0.0` to `1.0`)
  - `aliases` (list of strings): Alternative name variants identified during resolution
  - `source_files` (list of strings): List of filenames mentioning this person
  - `status` (string): Processing status (`"VERIFIED"` \| `"REVIEW_REQUIRED"`)
  - `risk_color` (string): UI risk indicator (`"none"` \| `"orange"` \| `"red"`)
  - `historical_firs` (integer): Count of associated FIR records
- **Created in**: [`backend/app/ingestion/ner.py:L301`](file:///d:/SIH2026/backend/app/ingestion/ner.py#L301), [`backend/app/database/neo4j.py:L26`](file:///d:/SIH2026/backend/app/database/neo4j.py#L26)

### 3. `PHONE`
- **Primary Key / Merge Query**: `id` (e.g. `phone:f3a47ce5`)
- **Properties**:
  - `id` (string): Unique identifier (e.g. `phone:+919876543210`)
  - `value` (string): Normalized E.164 phone string (e.g. `+919876543210`)
  - `type` (string): `"PHONE"`
  - `confidence` (float): `0.9` to `1.0`
  - `source_files` (list of strings): Originating document filenames
- **Created in**: [`backend/app/ingestion/ner.py:L227`](file:///d:/SIH2026/backend/app/ingestion/ner.py#L227), [`backend/app/database/neo4j.py:L26`](file:///d:/SIH2026/backend/app/database/neo4j.py#L26)

### 4. `VEHICLE`
- **Primary Key / Merge Query**: `id` (e.g. `vehicle:mh12ab1234`)
- **Properties**:
  - `id` (string): Unique identifier
  - `value` (string): Standardized vehicle registration string (e.g. `MH-12-AB-1234`)
  - `type` (string): `"VEHICLE"`
  - `confidence` (float): `0.9`
  - `source_files` (list of strings): Originating document filenames
- **Created in**: [`backend/app/ingestion/ner.py:L397`](file:///d:/SIH2026/backend/app/ingestion/ner.py#L397), [`backend/app/database/neo4j.py:L26`](file:///d:/SIH2026/backend/app/database/neo4j.py#L26)

### 5. `LOCATION`
- **Primary Key / Merge Query**: `id` (e.g. `location:hyderabad`)
- **Properties**:
  - `id` (string): Unique identifier
  - `value` (string): Location name (e.g. `Hyderabad`)
  - `type` (string): `"LOCATION"`
  - `confidence` (float): `0.85`
  - `source_files` (list of strings): Originating document filenames
- **Created in**: [`backend/app/ingestion/ner.py:L440`](file:///d:/SIH2026/backend/app/ingestion/ner.py#L440), [`backend/app/database/neo4j.py:L26`](file:///d:/SIH2026/backend/app/database/neo4j.py#L26)

### 6. `ACCOUNT`
- **Primary Key / Merge Query**: `id` (e.g. `account:acc_ahmed_4521`)
- **Properties**:
  - `id` (string): Unique identifier
  - `value` (string): Normalized account number (e.g. `ACC-AHMED-4521`)
  - `type` (string): `"ACCOUNT"`
  - `confidence` (float): `1.0`
  - `source_files` (list of strings): Originating document filenames
- **Created in**: [`backend/app/ingestion/ner.py:L266`](file:///d:/SIH2026/backend/app/ingestion/ner.py#L266), [`backend/app/database/neo4j.py:L26`](file:///d:/SIH2026/backend/app/database/neo4j.py#L26)

### 7. `ORG`
- **Primary Key / Merge Query**: `id` (e.g. `org:crescent_traders`)
- **Properties**:
  - `id` (string): Unique identifier
  - `value` (string): Organization name (e.g. `Crescent Traders`)
  - `type` (string): `"ORG"`
  - `confidence` (float): `0.85`
  - `source_files` (list of strings): Originating document filenames
- **Created in**: [`backend/app/ingestion/ner.py:L444`](file:///d:/SIH2026/backend/app/ingestion/ner.py#L444), [`backend/app/database/neo4j.py:L26`](file:///d:/SIH2026/backend/app/database/neo4j.py#L26)

### 8. `FIR`
- **Primary Key / Merge Query**: `id` (e.g. `fir:fir_002_andheri`)
- **Properties**:
  - `id` (string): Unique identifier
  - `value` (string): FIR reference identifier
  - `type` (string): `"FIR"`
  - `confidence` (float): `0.9`
  - `source_files` (list of strings): Originating document filenames
- **Created in**: [`backend/app/ingestion/ner.py:L402`](file:///d:/SIH2026/backend/app/ingestion/ner.py#L402), [`backend/app/database/neo4j.py:L26`](file:///d:/SIH2026/backend/app/database/neo4j.py#L26)

### 9. `AADHAAR`
- **Primary Key / Merge Query**: `id` (e.g. `aadhaar:<sha256_hash>`)
- **Properties**:
  - `id` (string): Unique identifier based on SHA-256 hash
  - `value` (string): Masked display string (e.g. `XXXX-XXXX-1234`)
  - `type` (string): `"AADHAAR"`
  - `confidence` (float): `0.9`
  - `sha256_hash` (string): SHA-256 hash of raw Aadhaar digits
- **Created in**: [`backend/app/ingestion/ner.py:L408`](file:///d:/SIH2026/backend/app/ingestion/ner.py#L408), [`backend/app/database/neo4j.py:L26`](file:///d:/SIH2026/backend/app/database/neo4j.py#L26)

---

## Relationship types currently produced by the live pipeline

All relationships are persisted in [`backend/app/database/neo4j.py:L68-L88`](file:///d:/SIH2026/backend/app/database/neo4j.py#L68-L88) via `MERGE (source)-[r:<TYPE>]->(target)`.

| Relationship Type | Source Label | Target Label | Properties | Description / Origin File |
|---|---|---|---|---|
| `EXTRACTED_FROM` | `ANY_ENTITY` | `Document` | None | Provenance edge created in [`backend/app/database/neo4j.py:L44`](file:///d:/SIH2026/backend/app/database/neo4j.py#L44). |
| `CALLED` | `PHONE` | `PHONE` | `confidence`, `status`, `evidence`, `timestamp`, `duration`, `location` | Structured CDR call record ([`ner.py:L244`](file:///d:/SIH2026/backend/app/ingestion/ner.py#L244)). |
| `TRANSFERRED_TO` | `ACCOUNT` | `ACCOUNT` | `confidence`, `status`, `evidence`, `amount`, `timestamp` | Financial bank statement transaction ([`ner.py:L286`](file:///d:/SIH2026/backend/app/ingestion/ner.py#L286)). |
| `HAS_PHONE` | `PERSON` | `PHONE` | `confidence`, `status`, `evidence` | Co-occurrence of Person and Phone in same sentence ([`ner.py:L508`](file:///d:/SIH2026/backend/app/ingestion/ner.py#L508)). |
| `OWNS_VEHICLE` | `PERSON` | `VEHICLE` | `confidence`, `status`, `evidence` | Co-occurrence of Person and Vehicle in text ([`ner.py:L518`](file:///d:/SIH2026/backend/app/ingestion/ner.py#L518)). |
| `ASSOCIATED_WITH` | `PERSON` | `ORG` | `confidence`, `status`, `evidence` | Co-occurrence of Person and Organization ([`ner.py:L528`](file:///d:/SIH2026/backend/app/ingestion/ner.py#L528)). |
| `MENTIONED_NEAR` | `PERSON` | `LOCATION` | `confidence`, `status`, `evidence` | Co-occurrence of Person and Location ([`ner.py:L538`](file:///d:/SIH2026/backend/app/ingestion/ner.py#L538)). |
| `COMMUNICATED_WITH` | `PHONE` | `PHONE` | `confidence`, `status`, `evidence` | Co-occurrence of multiple phones in unstructured text ([`ner.py:L551`](file:///d:/SIH2026/backend/app/ingestion/ner.py#L551)). |
| `MENTIONED_IN` | `ANY_ENTITY` | `FIR` | `confidence`, `status`, `evidence` | Link between extracted entity and FIR node ([`ner.py:L585`](file:///d:/SIH2026/backend/app/ingestion/ner.py#L585)). |
| `<VERB_TRIGGER>` (Dynamic) | `ANY_ENTITY` | `ANY_ENTITY` | `confidence`, `status`, `evidence`, `trigger_verb` | Dynamic upper-case relationship from sentence verbs (e.g., `MET`, `PAID`, `OPERATES`) ([`ner.py:L569`](file:///d:/SIH2026/backend/app/ingestion/ner.py#L569)). |

---

## Node/relationship types defined in synthetic data but not yet in the live pipeline

The synthetic data generator in [`graph/generate_anomaly_data.py`](file:///d:/SIH2026/graph/generate_anomaly_data.py) defines mock graphs using relationship types and node structures that differ from the live pipeline:

1. **`TRANSACTION` Relationship**:
   - **Source -> Target**: `PERSON` -> `PERSON` (or `ACCOUNT` -> `ACCOUNT`)
   - **Properties**: `id`, `timestamp`, `amount`
   - **File**: [`graph/generate_anomaly_data.py:L48`](file:///d:/SIH2026/graph/generate_anomaly_data.py#L48)
   - *Status*: Generator-only. Live ingestion uses `TRANSFERRED_TO` between `ACCOUNT` nodes.

2. **`CALL` Relationship**:
   - **Source -> Target**: `PERSON` -> `PERSON` (or `PHONE` -> `PHONE`)
   - **Properties**: `id`, `timestamp`, `duration`
   - **File**: [`graph/generate_anomaly_data.py:L57`](file:///d:/SIH2026/graph/generate_anomaly_data.py#L57)
   - *Status*: Generator-only. Live ingestion uses `CALLED` or `COMMUNICATED_WITH` between `PHONE` nodes.

3. **`PERSON_001` ID Format**:
   - **File**: [`graph/generate_anomaly_data.py:L28`](file:///d:/SIH2026/graph/generate_anomaly_data.py#L28)
   - *Status*: Generator uses flat uppercase strings (e.g. `PERSON_001`). Live ingestion uses lowercase typed prefixes with MD5 hashes (e.g. `person:a7ca11a0`).

---

## Confirmed mismatches between generator, ingestion, and read queries

1. **Relationship Naming Mismatch**:
   - `graph/generate_anomaly_data.py` emits relationship types `TRANSACTION` and `CALL`.
   - `backend/app/ingestion/ner.py` emits relationship types `TRANSFERRED_TO` and `CALLED`/`COMMUNICATED_WITH`.
   - *Impact*: Code written to query `TRANSACTION` or `CALL` edges will return 0 results against real ingested graph data.

2. **Read Query Provenance Dependency**:
   - `get_case_graph()` in [`backend/app/main.py:L42-L55`](file:///d:/SIH2026/backend/app/main.py#L42-L55) queries nodes using:
     `MATCH (n)-[:EXTRACTED_FROM]->(:Document {case_id: $case_id})`
   - *Impact*: If synthetic graph nodes are inserted into Neo4j without a `Document` node and `EXTRACTED_FROM` relationship, `get_case_graph()` returns an empty node set (`nodes: [], edges: []`).

3. **Node ID Format Mismatch**:
   - `generate_anomaly_data.py` produces `PERSON_001`.
   - Ingestion resolver (`resolver.py`) produces `person:a7ca11a0` or `phone:f3a47ce5`.

---

## Example queries actually used in the codebase

### Query 1: Fetching Case Graph Nodes
From [`backend/app/main.py:L42-L47`](file:///d:/SIH2026/backend/app/main.py#L42-L47):
```cypher
MATCH (n)-[:EXTRACTED_FROM]->(:Document {case_id: $case_id})
RETURN DISTINCT n.id AS id, n.value AS value,
       labels(n)[0] AS type, n.confidence AS confidence,
       n.status AS status, n.risk_color AS risk_color,
       n.historical_firs AS historical_firs
```

### Query 2: Fetching Case Graph Edges
From [`backend/app/main.py:L52-L56`](file:///d:/SIH2026/backend/app/main.py#L52-L56):
```cypher
MATCH (a)-[:EXTRACTED_FROM]->(:Document {case_id: $case_id})
MATCH (a)-[r]->(b) WHERE type(r) <> 'EXTRACTED_FROM'
RETURN a.id AS source, b.id AS target, type(r) AS type,
       r.confidence AS confidence, r.status AS status, r.evidence AS evidence
```

### Query 3: Entity Node Ingestion & Property Set
From [`backend/app/database/neo4j.py:L28-L39`](file:///d:/SIH2026/backend/app/database/neo4j.py#L28-L39):
```cypher
MERGE (n:PERSON {id: $id})
SET n.value = $value,
    n.confidence = $confidence,
    n += $attributes
```

### Query 4: Document Linkage Ingestion
From [`backend/app/database/neo4j.py:L44-L45`](file:///d:/SIH2026/backend/app/database/neo4j.py#L44-L45):
```cypher
MATCH (n {id: $id}), (d:Document {file_name: $file_name, case_id: $case_id})
MERGE (n)-[:EXTRACTED_FROM]->(d)
```

---

## Conventions observed

- **Node Label Casing**:
  - `Document`: PascalCase.
  - Entity Labels: ALL-CAPS single words (`PERSON`, `PHONE`, `VEHICLE`, `LOCATION`, `ACCOUNT`, `ORG`, `FIR`, `AADHAAR`).
- **Relationship Type Casing**:
  - ALL-CAPS `SNAKE_CASE` (e.g., `EXTRACTED_FROM`, `TRANSFERRED_TO`, `CALLED`, `HAS_PHONE`, `OWNS_VEHICLE`, `COMMUNICATED_WITH`).
- **Identity & Uniqueness**:
  - Nodes use a unique `id` property formatted as `<type>:<hash_or_value>` (e.g. `person:a7ca11a0`, `phone:+919876543210`).
  - `MERGE` queries in `neo4j.py` always match on `{id: $id}`.
- **Document Provenance**:
  - Every ingested entity node `n` maintains an explicit `EXTRACTED_FROM` relationship pointing to its originating `(d:Document {file_name, case_id})` node.
- **Confidence Representation**:
  - Floating-point number between `0.0` and `1.0` stored on `n.confidence` and `r.confidence`.
