# API Endpoint Reference

Complete documentation for all endpoints exposed by the VERITAS FastAPI backend service (`http://localhost:8000/api`).

Source Code: [`backend/app/main.py`](file:///d:/SIH2026/backend/app/main.py), [`backend/app/api/`](file:///d:/SIH2026/backend/app/api/)

---

## 1. System & Health

### `GET /`
- **Description**: Root status check.
- **Auth**: None
- **Response `200 OK`**:
```json
{
  "status": "ok",
  "service": "CIAS ML Backend"
}
```

### `GET /health`
- **Description**: Service liveness & readiness check.
- **Auth**: None
- **Response `200 OK`**:
```json
{
  "status": "healthy"
}
```

---

## 2. Authentication (`/api/auth`)

### `POST /api/auth/register`
- **Description**: Registers a new system user.
- **Auth**: None
- **Request Body** (`UserCreate`):
```json
{
  "username": "arjun.rao",
  "password": "SecurePassword123",
  "full_name": "Inspector Arjun Rao",
  "role": "investigator"
}
```
- **Response `200 OK`** (`UserOut`):
```json
{
  "id": "e4b3c2a1-0000-0000-0000-123456789abc",
  "username": "arjun.rao",
  "full_name": "Inspector Arjun Rao",
  "role": "investigator"
}
```

### `POST /api/auth/login`
- **Description**: Authenticates user and issues OAuth2 Bearer JWT.
- **Auth**: None (Form Data: `username`, `password`)
- **Response `200 OK`**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "e4b3c2a1-0000-0000-0000-123456789abc",
    "username": "rao.a",
    "full_name": "Inspector Arjun Rao",
    "role": "investigator"
  }
}
```

### `GET /api/auth/me`
- **Description**: Fetches current authenticated user profile.
- **Auth**: Bearer JWT

---

## 3. Evidence Ingestion & Pipeline (`/api`)

### `POST /api/process-evidence`
- **Description**: Main ingestion pipeline entry point. Uploads FIRs, CDRs, bank ledgers, or case files (PDF, DOCX, CSV, JSON, TXT) and triggers the 7-stage pipeline.
- **Auth**: Bearer JWT
- **Form Data**:
  - `files`: `List[UploadFile]` (Binary files)
  - `case_id`: `string` (e.g. `"CASE-102"`)
  - `sync`: `boolean` (Default: `false`)
- **Response `200 OK` (Async Mode - Default)**:
```json
{
  "job_id": "job-a1b2c3d4",
  "status": "queued",
  "stage": 0,
  "stage_name": "Ingest",
  "message": "Pipeline processing enqueued in background. Real-time updates pushed via WebSocket/Job API."
}
```
- **Response `200 OK` (Sync Mode)**: Returns complete graph nodes, links, ingestion status, and disambiguation review queue items.

### `GET /api/pipeline/jobs/{job_id}`
- **Description**: Polls job progress, logs, and stage completion.
- **Auth**: None / Optional

### `WS /api/pipeline/ws/{job_id}`
- **Description**: Real-time WebSocket connection delivering live stage execution updates (0. Ingest -> 1. Normalize -> 2. Extract -> 3. Resolve -> 4. Graph -> 5. Analyze -> 6. Explain -> 7. Complete).

---

## 4. Cases (`/api/cases`)

### `POST /api/cases`
- **Description**: Creates a new investigation case.
- **Auth**: Bearer JWT (Role: `investigator`, `supervisor`, `system_admin`)

### `GET /api/cases`
- **Description**: Lists cases assigned to or accessible by the user.
- **Auth**: Bearer JWT

### `GET /api/cases/{case_id}/graph`
- **Description**: Queries Neo4j for nodes and edges associated with a specific case.
- **Auth**: Bearer JWT (ABAC Case Access)
- **Response `200 OK`**:
```json
{
  "case_id": "CASE-102",
  "nodes": [
    {
      "id": "person:a7ca11a0",
      "value": "Faisal Khan",
      "type": "PERSON",
      "confidence": 0.95,
      "status": "REVIEW_REQUIRED",
      "risk_color": "red",
      "historical_firs": 2,
      "phone": "+919876543210",
      "anomaly_reasons": ["Implicated across 3 distinct evidence types."],
      "evidence_trail": ["FIR Record: FIR_001.pdf", "CDR: +919876543210"],
      "flagged": true
    }
  ],
  "edges": [
    {
      "source": "person:a7ca11a0",
      "target": "phone:f3a47ce5",
      "type": "HAS_PHONE",
      "relationship_type": "HAS_PHONE",
      "confidence": 0.9,
      "status": "VERIFIED",
      "evidence": "FIR_001.pdf"
    }
  ]
}
```

---

## 5. Entity Disambiguation & Review Queue (`/api`)

### `GET /api/review-queue`
- **Description**: Lists pending ambiguous identity matches requiring human investigator review.
- **Auth**: None / Optional
- **Response `200 OK`**:
```json
{
  "total": 1,
  "pending_review": [
    {
      "type": "PERSON_NAME_AMBIGUITY",
      "candidate": { "id": "person:a7ca11a0", "value": "Faisal Khan" },
      "possible_match": { "id": "person:b8db22b1", "value": "Faizal Cahn" },
      "confidence": 0.78,
      "reasons": ["Phonetic Double Metaphone match (FS LK)", "Jaro-Winkler score 0.81"]
    }
  ]
}
```

### `POST /api/review-queue/{review_id}/resolve`
- **Description**: Resolves a review item (`action`: `"merge"`, `"reject"`, or `"skip"`). Action `"merge"` triggers automated Neo4j node consolidation.
- **Auth**: Bearer JWT (Role: `investigator`, `supervisor`, `system_admin`)

---

## 6. Evidence Integrity & Ledger (`/api/evidence`)

### `GET /api/evidence/ledger`
- **Description**: Retrieves the complete evidence ledger including SHA-256 digests and Merkle Tree root hashes.
- **Auth**: None / Optional

### `POST /api/evidence/verify`
- **Description**: Verifies an uploaded document's SHA-256 hash against the tamper-evident ledger.
- **Request Body**:
```json
{
  "file_name": "FIR_001_Faisal_Khan.pdf",
  "file_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "case_id": "CASE-102"
}
```
- **Response `200 OK`**:
```json
{
  "verified": true,
  "status": "MATCH_CONFIRMED",
  "record": {
    "record_id": "EV-E3B0C442",
    "file_name": "FIR_001_Faisal_Khan.pdf",
    "case_id": "CASE-102",
    "file_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "merkle_root": "a8f9b2c3...",
    "timestamp": "2026-09-04T12:00:00.000Z",
    "status": "VERIFIED_TAMPER_EVIDENT"
  }
}
```

### `GET /api/evidence/{case_id}/integrity`
- **Description**: Retrieves the Merkle Root Hash and evidence checksum tree for a specific case.

---

## 7. Anomaly & Graph Analytics (`/api`)

### `GET /api/anomalies`
- **Description**: Fetches all persisted rule-based and Isolation Forest anomaly alerts.

### `GET /api/cases/{case_id}/anomalies`
- **Description**: Computes real-time rule and ML anomaly scores for a case network.

### `GET /api/cases/{case_id}/analytics`
- **Description**: Computes PageRank, Betweenness Centrality, Communities, and degree metrics for a case graph.

### `GET /api/analytics/shortest-path`
- **Description**: Traces shortest path and distance between `source` and `target` entities.
