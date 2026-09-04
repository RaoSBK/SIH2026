# PROJECT_CONTEXT.md

Last verified: 2026-09-04

## What CIAS is
CIAS (Criminal Intelligence Analysis System / VERITAS) is a FastAPI-based web application and single-page HTML/D3.js visualization console for crime investigation data processing. It ingests unstructured case documents (PDF, DOCX, CSV, JSON, TXT), extracts entities (persons, phone numbers, vehicles, locations, events) and relationships via spaCy and regular expressions, deduplicates entities into a unified graph stored in Neo4j, and renders an interactive force-directed graph canvas alongside investigator review queues.

## What's actually working end-to-end today
- **Multi-Format Document Ingestion**: Uploading PDF, DOCX, CSV, JSON, and TXT files via `POST /api/process-evidence` in [`backend/app/main.py`](file:///d:/SIH2026/backend/app/main.py#L75-L156). File handling is dispatched via [`backend/app/ingestion/service.py`](file:///d:/SIH2026/backend/app/ingestion/service.py#L13-L116) to parsers in [`pdf_parser.py`](file:///d:/SIH2026/backend/app/ingestion/parsers/pdf_parser.py), [`docx_parser.py`](file:///d:/SIH2026/backend/app/ingestion/parsers/docx_parser.py), [`csv_parser.py`](file:///d:/SIH2026/backend/app/ingestion/parsers/csv_parser.py), [`json_parser.py`](file:///d:/SIH2026/backend/app/ingestion/parsers/json_parser.py), and [`txt_parser.py`](file:///d:/SIH2026/backend/app/ingestion/parsers/txt_parser.py).
- **Rule-based & spaCy Entity Extraction**: Text entity recognition (Person, Phone, Vehicle, Location, Event) and relationship linkage implemented in [`backend/app/ingestion/ner.py`](file:///d:/SIH2026/backend/app/ingestion/ner.py#L1-L629).
- **Multi-Signal Entity Resolution & Review Queueing**: Phonetic/fuzzy name matching, phone number merging, case-corroborated deduplication, and flagging ambiguous identity matches into `needs_review` structures in [`backend/app/ingestion/resolver.py`](file:///d:/SIH2026/backend/app/ingestion/resolver.py#L1-L694).
- **Neo4j Graph Database Persistence**: Node and edge persistence with document provenance linkage (`:EXTRACTED_FROM`) using official Cypher driver queries in [`backend/app/database/neo4j.py`](file:///d:/SIH2026/backend/app/database/neo4j.py#L10-L126).
- **FastAPI Backend API**: Live routes in [`backend/app/main.py`](file:///d:/SIH2026/backend/app/main.py):
  - `GET /` (root status check)
  - `GET /api/cases/{case_id}/graph` (queries Neo4j for nodes and edges linked to a case)
  - `POST /api/process-evidence` (file upload and ingestion pipeline execution)
  - `GET /api/ingestion-audit` (reads JSON audit log)
  - `GET /api/needs-review` & `GET /api/review-queue` (lists pending entity disambiguation items)
  - `GET /api/filtered-edges` (lists audit trail of removed self-loops or conflicted edges)
  - `POST /api/review-queue/{review_id}/resolve` (resolves or dismisses pending review items in local registry)
- **JSON File-Based Audit Logging**: Ingestion logs, filtered edge logs, and entity registry state persisted to local JSON files (`data/ingestion_audit.json`, `data/filtered_edges.json`, `data/entity_registry.json`) via [`backend/app/audit/logger.py`](file:///d:/SIH2026/backend/app/audit/logger.py#L28-L90).
- **Single-Page HTML/D3.js Investigator Console**: Static frontend dashboard rendering graph visualizer, case metrics, file uploader, and review queue in [`frontend/index.html`](file:///d:/SIH2026/frontend/index.html) (838 lines) and [`frontend/graph/graph.js`](file:///d:/SIH2026/frontend/graph/graph.js) (also replicated at root [`index.html`](file:///d:/SIH2026/index.html)).

## What exists as real code but is NOT connected to the app
- **`ml/processor.py`** (238 lines) & **`ml/nlp/cias_nlp.py`** (166 lines): Legacy standalone ML pipeline for spaCy NER, OCR noise cleaning, and RapidFuzz entity matching. Dropped during backend unification in commit `056c837` in favor of `backend/app/ingestion/`. *To wire in*: Replace calls in `backend/app/ingestion/service.py` to import `ml.processor` functions.
- **`ml/anomaly/anomaly_ml.py`** (123 lines) & **`ml/anomaly/anomaly_rules.py`** (160 lines): Anomaly detection pipeline implementing Isolation Forest models and network rule scoring. Not called by `main.py` (which uses a basic connection-count heuristic on lines 135-149 of `main.py`). *To wire in*: Import `anomaly_ml` or `anomaly_rules` into `main.py` during graph post-processing.
- **`cias_er/` module** ([`clustering.py`](file:///d:/SIH2026/cias_er/clustering.py) [105 lines], [`matcher.py`](file:///d:/SIH2026/cias_er/matcher.py) [74 lines], [`pipeline.py`](file:///d:/SIH2026/cias_er/pipeline.py) [43 lines], [`process_dataset.py`](file:///d:/SIH2026/cias_er/process_dataset.py) [76 lines]): Separate Python package for entity resolution using Jaro-Winkler scoring and agglomerative clustering. Has its own test (`cias_er/tests/test_pipeline.py`) but is not imported anywhere in `backend/app/`. *To wire in*: Replace `resolve_entities` in `backend/app/ingestion/resolver.py` with `cias_er.pipeline.resolve_entities`.
- **`graph/generate_anomaly_data.py`** (115 lines), **`graph/generate_synthetic_data.py`** (195 lines), **`graph/validate_synthetic_data.py`** (165 lines): Offline synthetic graph generation and validation scripts. Not connected to FastAPI endpoints.
- **`scripts/generate_evidence_pdfs.py`** (140 lines) & **`scripts/generate_training_data.py`** (103 lines): Standalone synthetic PDF and training data generators.

## What's a placeholder / stub only
A file is classified as a stub if it contains under 10-15 lines consisting only of docstrings, module headers (`# -*- coding: utf-8 -*-`), or empty `pass` statements without logic.

- **`backend/app/`**: **55 stubs / 70 code files** (78.5% stubs).
  - All files in `api/` (`analytics.py`, `anomaly.py`, `audit.py`, `auth.py`, `cases.py`, `entities.py`, `evidence.py`, `graph.py`, `ingestion.py`, `router.py`, `users.py`)
  - All files in `auth/` (`abac.py`, `authentication.py`, `authorization.py`, `jwt.py`, `rbac.py`)
  - All files in `cases/` (`models.py`, `repository.py`, `schemas.py`, `service.py`)
  - All files in `entities/` (`models.py`, `schemas.py`, `service.py`)
  - All files in `evidence/` (`models.py`, `schemas.py`, `service.py`, `storage.py`)
  - All files in `users/` (`models.py`, `schemas.py`, `service.py`)
  - All files in `integrations/` (`analytics_client.py`, `blockchain_client.py`, `graph_client.py`, `nlp_client.py`)
  - All files in `utils/` (`exceptions.py`, `hashing.py`, `validators.py`)
  - All files in `config/` (`logging.py`, `settings.py`)
  - Database stubs: `database/postgres.py`, `database/redis.py`
- **`blockchain/`**: **9 stubs / 9 code files** (100% stubs).
  - `fabric_client.py`, `chaincode/audit/chaincode.py`, `chaincode/evidence/chaincode.py`, `chaincode/evidence/models.py`, `merkle_tree.py`, `sha256.py`, `test_integrity.py`, `verify_hash.py`, `verify_merkle.py` are all 6-line docstring stubs. 0% implementation in code.
- **`ml/`**: **36 stubs / 44 code files** (81.8% stubs).
  - Stubs in `ml/anomaly/features/`, `ml/anomaly/models/`, `ml/anomaly/rules/`, `ml/common/`, `ml/nlp/entity_normalization/`, `ml/nlp/entity_resolution/`, `ml/nlp/ner/` (`inference.py`, `labels.py`, `model.py`), `ml/nlp/preprocessing/` (`cleaner.py`, `language_detector.py`, `tokenizer.py`), `ml/nlp/relation_extraction/`, `ml/temporal/`.
- **`graph/`**: **13 stubs / 16 code files** (81.3% stubs).
  - Stubs in `graph/analytics/` (`betweenness.py`, `communities.py`, `degree.py`, `pagerank.py`, `paths.py`, `temporal.py`), `graph/ingestion/` (`edge_builder.py`, `graph_loader.py`, `node_builder.py`), `graph/services/` (`analytics_service.py`, `graph_service.py`), `graph/tests/` (`test_analytics.py`, `test_graph.py`).
- **`tests/` (root)**: **11 stubs / 11 code files** (100% stubs).
  - All test files in `tests/e2e/`, `tests/integration/`, `tests/performance/`, `tests/security/` are 6-line header stubs.
- **`scripts/`**: **4 stubs / 6 code files** (66.7% stubs).
  - `generate-demo-data.py`, `health-check.py`, `seed-database.py`, `seed-graph.py` are 6-line header stubs.
- **`.github/workflows/`**: **4 empty files / 4 workflow files** (100% empty).
  - `backend-tests.yml`, `build.yml`, `frontend-tests.yml`, `ml-tests.yml` contain only 2-line comment headers.

## Duplicate or competing implementations
Three distinct entity resolution / NLP extraction implementations exist in the repository:
1. **Canonical / Live Pipeline**: [`backend/app/ingestion/ner.py`](file:///d:/SIH2026/backend/app/ingestion/ner.py) (629 lines) + [`backend/app/ingestion/resolver.py`](file:///d:/SIH2026/backend/app/ingestion/resolver.py) (694 lines). Wired directly to `POST /api/process-evidence` in `main.py` via `backend/app/ingestion/service.py`.
2. **Standalone ER Pipeline**: `cias_er/` ([`clustering.py`](file:///d:/SIH2026/cias_er/clustering.py), [`matcher.py`](file:///d:/SIH2026/cias_er/matcher.py), [`pipeline.py`](file:///d:/SIH2026/cias_er/pipeline.py)). Uses Jaro-Winkler distance and agglomerative clustering. Unconnected to backend.
3. **Legacy ML Pipeline**: [`ml/processor.py`](file:///d:/SIH2026/ml/processor.py) (238 lines) & [`ml/nlp/cias_nlp.py`](file:///d:/SIH2026/ml/nlp/cias_nlp.py) (166 lines). Early spaCy NER and OCR noise cleaner. Unconnected to backend.

## Infrastructure reality
`docker-compose.yml` configures 4 services:
- `backend`: FastAPI app (`uvicorn backend.app.main:app`) on port 8000.
- `frontend`: Nginx static web server (`infrastructure/docker/frontend.Dockerfile`) on port 3000.
- `postgres`: PostgreSQL 15 container (`postgres:15-alpine`) on port 5432.
- `neo4j`: Neo4j container with APOC plugin (`infrastructure/docker/neo4j.Dockerfile`) on ports 7474/7687.

**Infrastructure Gaps vs Folder Structure**:
- **No ML Service**: `ml` is mounted into the backend container; there is no separate ML service container.
- **No Blockchain Node**: No Hyperledger Fabric or blockchain container exists in `docker-compose.yml`.
- **No Redis Cache**: Redis is not configured in `docker-compose.yml` (`backend/app/database/redis.py` is a stub).
- **No Separate Graph Microservice**: Neo4j runs as a database container, but graph operations are queried directly by FastAPI rather than a distinct microservice.

## Test & CI status
- **Test File Inventory**: 27 test files exist across the workspace. 22 of 27 test files are 6-line empty stubs.
- **Active Test Suites**:
  - [`backend/tests/test_pipeline.py`](file:///d:/SIH2026/backend/tests/test_pipeline.py) (285 lines, 15 tests)
  - [`cias_er/tests/test_pipeline.py`](file:///d:/SIH2026/cias_er/tests/test_pipeline.py) (41 lines, 1 test)
  - [`ml/anomaly/tests/test_anomalies.py`](file:///d:/SIH2026/ml/anomaly/tests/test_anomalies.py) (55 lines, 1 test)
  - [`ml/nlp/tests/test_nlp.py`](file:///d:/SIH2026/ml/nlp/tests/test_nlp.py) (58 lines, 1 test)
- **Empirical Execution Result**: `python -m pytest` yielded **9 passed, 9 failed**. Failures stem from:
  - Refactored function names in `ner.py` (`_is_probable_name` moved/removed)
  - Missing mock target in `resolver.py` (`log_filtered_edge`)
  - RapidFuzz version mismatch in `cias_er/matcher.py` (`fuzz.jaro_winkler_similarity`)
  - Extra trailing data in `ml/anomaly/tests/mock_graph.json`
- **CI Status**: `.github/workflows/` files (`backend-tests.yml`, `build.yml`, `frontend-tests.yml`, `ml-tests.yml`) are 2-line empty stubs. CI does not execute on GitHub Actions.

## Known gaps vs. the pitched design
- **Frontend Framework Switch**: `frontend/package.json` specifies a React 19 + Cytoscape + Tailwind SPA, but `frontend/src/` is absent. The application actually renders via a standalone single-page HTML/D3.js file (`frontend/index.html`).
- **Blockchain Evidence Integrity**: `blockchain/` folder is 100% stubs (0/9 implemented files). Merkle tree verification and Hyperledger Fabric integration do not exist in code.
- **Relational PostgreSQL Persistence**: `backend/app/database/postgres.py` is a stub. Ingestion audit logs, entity registries, and review queues are saved to flat JSON files (`data/ingestion_audit.json`, `data/entity_registry.json`).
- **Authentication & RBAC**: `backend/app/auth/` (JWT, RBAC, ABAC) and `backend/app/users/` are 100% stubs. API routes in `main.py` are open without authentication or role verification.
- **Modular FastAPI Router Architecture**: All active endpoints are defined directly inside `backend/app/main.py`. The modular router structure in `backend/app/api/` is entirely stubs.
- **ML Anomaly Service**: `ml/anomaly/anomaly_ml.py` (Isolation Forest) is disconnected from the running app; `main.py` flags anomalies using a static node degree count threshold instead.
