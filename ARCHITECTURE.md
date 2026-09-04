# ARCHITECTURE.md

Last verified: 2026-09-04

## System diagram (as text, since this may render without image support)

```mermaid
graph TD
    Client["Browser / Investigator Console<br>(Static Single-Page App)"]
    Frontend["Nginx Web Server<br>(cias_frontend:3000)"]
    Backend["FastAPI Backend<br>(cias_backend:8000)"]
    Neo4j[("Neo4j Graph Database<br>(cias_neo4j:7687/7474)")]
    Postgres[("PostgreSQL 15 Database<br>(cias_postgres:5432)")]
    LocalJSON[("Flat JSON Storage<br>data/*.json")]

    Client -- "Loads HTML/CSS/D3 assets" --> Frontend
    Client -- "POST /api/process-evidence<br>GET /api/cases/{case_id}/graph<br>POST /api/review-queue/{id}/resolve" --> Backend
    Backend -- "Cypher query execution via bolt://neo4j:7687" --> Neo4j
    Backend -. "DATABASE_URL set in env<br>(0 queries executed / stub interface)" .-> Postgres
    Backend -- "File I/O audit logs & entity registry" --> LocalJSON
```

## Services that exist and run
As defined in [`docker-compose.yml`](file:///d:/SIH2026/docker-compose.yml), the application deploys exactly four Docker containers:

1. **`backend` (`cias_backend`)**:
   - **Role**: Core FastAPI web server running `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`.
   - **Port**: `8000`
   - **Dependencies**: Depends on `postgres` (healthy) and `neo4j` (healthy).
   - **Volume Mounts**: Mounts `./backend`, `./ml`, and `./data` into `/app/`.
   - **Environment**: Sets `DATABASE_URL=postgresql://postgres:postgres@postgres:5432/criminal_intel` and `NEO4J_URI=bolt://neo4j:7687`.

2. **`frontend` (`cias_frontend`)**:
   - **Role**: Nginx web server built via [`infrastructure/docker/frontend.Dockerfile`](file:///d:/SIH2026/infrastructure/docker/frontend.Dockerfile) serving static HTML, CSS, and D3 JavaScript files.
   - **Port**: `3000`
   - **Dependencies**: Depends on `backend`.

3. **`neo4j` (`cias_neo4j`)**:
   - **Role**: Graph database built via [`infrastructure/docker/neo4j.Dockerfile`](file:///d:/SIH2026/infrastructure/docker/neo4j.Dockerfile) with APOC procedures enabled (`NEO4J_PLUGINS=["apoc"]`).
   - **Ports**: `7474` (HTTP Browser UI), `7687` (Bolt Binary Protocol).
   - **Healthcheck**: `cypher-shell -u neo4j -p password RETURN 1`.

4. **`postgres` (`cias_postgres`)**:
   - **Role**: Relational database running `postgres:15-alpine`.
   - **Port**: `5432`
   - **Healthcheck**: `pg_isready -U postgres`.

## Services implied by folder structure but NOT deployed
- **Standalone ML Microservice**: Implied by the `ml/` folder and `infrastructure/docker/ml.Dockerfile`, but `ml` is not declared as a separate container in `docker-compose.yml`. ML dependencies (spaCy, RapidFuzz) run inside the single `backend` container process.
- **Hyperledger Fabric Blockchain Service**: Implied by the `blockchain/` folder and documentation, but no Fabric peer, orderer, or CA containers exist in `docker-compose.yml`. Code files are 100% stubs.
- **Redis Cache & Queue**: Implied by `backend/app/database/redis.py`, but Redis is not present in `docker-compose.yml`. No in-memory cache or async task queue (e.g., Celery/Redis) is deployed.
- **Separate Graph Analytics Service**: Implied by `graph/services/` and `graph/analytics/`, but no separate service container exists; Neo4j queries are executed directly by the FastAPI backend process.
- **Auth & Identity Service**: Implied by `backend/app/auth/` and `backend/app/users/`, but no authentication container or service runs. All endpoints are currently open and unauthenticated.

## The real request flow: evidence upload → graph
The end-to-end evidence ingestion and graph rendering workflow executes synchronously through the following explicit sequence:

1. **UI Submission**: The investigator selects evidence files in the web interface or clicks the demo runner. The browser issues a `POST` request with `FormData` containing the file payloads and `case_id` to `http://localhost:8000/api/process-evidence` ([`frontend/index.html:L747`](file:///d:/SIH2026/frontend/index.html#L747)).
2. **FastAPI Endpoint Handling**: `process_evidence()` in [`backend/app/main.py:L76-L156`](file:///d:/SIH2026/backend/app/main.py#L76-L156) receives the files, saves them temporarily to `temp_uploads/`, and dispatches processing off the event loop via `asyncio.to_thread(process_file, temp_path, None, "investigator_upload", case_id)` ([`main.py:L97-L103`](file:///d:/SIH2026/backend/app/main.py#L97-L103)).
3. **Format Parsing**: `process_file()` in [`backend/app/ingestion/service.py:L13-L116`](file:///d:/SIH2026/backend/app/ingestion/service.py#L13-L116) detects the file extension and delegates to the appropriate parser ([`service.py:L31-L42`](file:///d:/SIH2026/backend/app/ingestion/service.py#L31-L42)):
   - PDF -> `parse_pdf()` in [`backend/app/ingestion/parsers/pdf_parser.py:L32`](file:///d:/SIH2026/backend/app/ingestion/parsers/pdf_parser.py#L32)
   - DOCX -> `parse_docx()` in [`backend/app/ingestion/parsers/docx_parser.py:L12`](file:///d:/SIH2026/backend/app/ingestion/parsers/docx_parser.py#L12)
   - CSV -> `parse_csv()` in [`backend/app/ingestion/parsers/csv_parser.py:L26`](file:///d:/SIH2026/backend/app/ingestion/parsers/csv_parser.py#L26)
   - JSON -> `parse_json()` in [`backend/app/ingestion/parsers/json_parser.py:L12`](file:///d:/SIH2026/backend/app/ingestion/parsers/json_parser.py#L12)
   - TXT -> `parse_txt()` in [`backend/app/ingestion/parsers/txt_parser.py:L8`](file:///d:/SIH2026/backend/app/ingestion/parsers/txt_parser.py#L8)
4. **Entity Extraction**: Parsed text is passed to `extract_entities()` in [`backend/app/ingestion/ner.py:L45`](file:///d:/SIH2026/backend/app/ingestion/ner.py#L45). It uses spaCy (`en_core_web_sm`) and regex rules to identify entities (`PERSON`, `PHONE`, `VEHICLE`, `LOCATION`, `EVENT`) and link relationships ([`service.py:L45`](file:///d:/SIH2026/backend/app/ingestion/service.py#L45)).
5. **Entity Resolution & Disambiguation**: Raw entities are passed to `resolve_entities()` in [`backend/app/ingestion/resolver.py:L50`](file:///d:/SIH2026/backend/app/ingestion/resolver.py#L50). It normalizes identifiers, merges duplicate phone/exact matches, checks case-corroboration signals, and flags ambiguous identity matches into `needs_review` payload structures ([`service.py:L50-L58`](file:///d:/SIH2026/backend/app/ingestion/service.py#L50-L58)).
6. **Neo4j Persistence**:
   - `delete_entities_by_source()` in [`backend/app/database/neo4j.py:L99-L126`](file:///d:/SIH2026/backend/app/database/neo4j.py#L99-L126) removes prior entity links associated with the document.
   - `insert_graph_data()` in [`backend/app/database/neo4j.py:L10-L98`](file:///d:/SIH2026/backend/app/database/neo4j.py#L10-L98) merges `Document` nodes, resolved entity nodes, and relationships (`:EXTRACTED_FROM`) into Neo4j via Cypher transactions ([`service.py:L63-L72`](file:///d:/SIH2026/backend/app/ingestion/service.py#L63-L72)).
7. **Audit Logging**: `log_ingestion()` in [`backend/app/audit/logger.py:L28-L44`](file:///d:/SIH2026/backend/app/audit/logger.py#L28-L44) appends ingestion metrics and status to `data/ingestion_audit.json` ([`service.py:L91-L99`](file:///d:/SIH2026/backend/app/ingestion/service.py#L91-L99)).
8. **Graph Fetch & Canvas Render**:
   - Upon receiving the `200 OK` response from `process-evidence`, the frontend fetches the complete case graph by making a `GET` request to `http://localhost:8000/api/cases/{caseId}/graph` ([`frontend/index.html:L764`](file:///d:/SIH2026/frontend/index.html#L764)).
   - `get_case_graph()` in [`backend/app/main.py:L30-L73`](file:///d:/SIH2026/backend/app/main.py#L30-L73) queries Neo4j for all nodes and edges linked to `Document {case_id}` and returns JSON.
   - D3.js scripts in [`frontend/graph/graph.js`](file:///d:/SIH2026/frontend/graph/graph.js) format the nodes and edges, rendering an interactive force-directed graph canvas.

## Data stores and what each one is actually used for today
- **Neo4j Database (`cias_neo4j`)**: **ACTIVE**. Neo4j is the primary knowledge graph store. It stores `Document` nodes, extracted entity nodes (`PERSON`, `PHONE`, `VEHICLE`, `LOCATION`, `EVENT`), entity relationships, and document provenance links (`:EXTRACTED_FROM`). Written by `insert_graph_data()` in [`backend/app/database/neo4j.py`](file:///d:/SIH2026/backend/app/database/neo4j.py) and read by `get_case_graph()` in [`backend/app/main.py`](file:///d:/SIH2026/backend/app/main.py).
- **PostgreSQL Database (`cias_postgres`)**: **DEPLOYED BUT UNUSED**. PostgreSQL 15 runs via `docker-compose.yml` and its connection string is supplied in the `backend` environment (`DATABASE_URL`). However, [`backend/app/database/postgres.py`](file:///d:/SIH2026/backend/app/database/postgres.py) is a 6-line stub. No backend route or service executes SQL queries against PostgreSQL.
- **Local Flat JSON Files**: **ACTIVE**. Serves as the primary operational store for audit trails and pending reviews:
  - `data/ingestion_audit.json`: Appended to by [`log_ingestion()`](file:///d:/SIH2026/backend/app/audit/logger.py#L28-L44), read by `GET /api/ingestion-audit`.
  - `data/filtered_edges.json`: Appended to by [`log_filtered_edge()`](file:///d:/SIH2026/backend/app/audit/logger.py#L47-L64), read by `GET /api/filtered-edges`.
  - `data/entity_registry.json`: Updated during resolution and review actions, read by `GET /api/needs-review` and `GET /api/review-queue`.
- **Redis Cache / Queue**: **NOT DEPLOYED / UNUSED**. Redis is not configured in `docker-compose.yml` and `backend/app/database/redis.py` is a 6-line stub.
- **MinIO / S3 Object Storage**: **NOT DEPLOYED / UNUSED**. Object storage is not deployed. Uploaded files are stored in temporary local directory `temp_uploads/` during processing and deleted immediately afterwards.

## Frontend ↔ backend contract
The frontend is a static single-page application ([`frontend/index.html`](file:///d:/SIH2026/frontend/index.html)) that communicates directly with the FastAPI backend. It hardcodes base URL `http://localhost:8000` and consumes three backend endpoints:

| Endpoint Call | HTTP Method | Frontend Invocation | Backend Handler |
|---|---|---|---|
| `/api/process-evidence` | `POST` | [`frontend/index.html:L747`](file:///d:/SIH2026/frontend/index.html#L747) | [`backend/app/main.py:L76`](file:///d:/SIH2026/backend/app/main.py#L76) (`process_evidence`) |
| `/api/cases/{case_id}/graph` | `GET` | [`frontend/index.html:L764`](file:///d:/SIH2026/frontend/index.html#L764) | [`backend/app/main.py:L30`](file:///d:/SIH2026/backend/app/main.py#L30) (`get_case_graph`) |
| `/api/review-queue/{review_id}/resolve` | `POST` | [`frontend/index.html:L496`](file:///d:/SIH2026/frontend/index.html#L496) | [`backend/app/main.py:L218`](file:///d:/SIH2026/backend/app/main.py#L218) (`resolve_review_item`) |

**Unconsumed Backend Endpoints**: `backend/app/main.py` also exposes `GET /`, `GET /api/ingestion-audit`, `GET /api/needs-review`, `GET /api/filtered-edges`, and `GET /api/review-queue`, but these are not currently invoked by `frontend/index.html`.

## Explicitly out of scope / not yet real
As documented in [`PROJECT_CONTEXT.md`](file:///d:/SIH2026/PROJECT_CONTEXT.md), the following components are stubs or unintegrated code and are not part of the active running system:
- **Blockchain Evidence Integrity**: `blockchain/` folder is 100% stubs (0/9 active files). No chaincode or Fabric SDK calls exist in runtime code.
- **Modular FastAPI Routers**: `backend/app/api/` router files are 6-line stubs. All active endpoints are in `main.py`.
- **PostgreSQL Audit & Case Management**: `backend/app/database/postgres.py` and repository classes in `cases/` and `evidence/` are stubs.
- **Authentication & RBAC**: `backend/app/auth/` (JWT, ABAC, RBAC) and `backend/app/users/` are 6-line stubs. Routes run without auth.
- **Standalone ML Services**: `ml/anomaly/anomaly_ml.py` and `cias_er/` pipeline are unintegrated standalone modules.

---

### Planned, not current
- **React 19 Frontend**: Migrating static `frontend/index.html` to a React 19 + Cytoscape + Tailwind SPA as declared in `frontend/package.json`.
- **PostgreSQL Database Integration**: Replacing flat JSON logs (`data/*.json`) with relational tables defined in `storage/postgres/schema.sql`.
- **Hyperledger Fabric Integration**: Connecting `blockchain/` chaincode stubs to secure evidence hashes.
- **Async Queue Architecture**: Introducing Redis and Celery/background workers for non-blocking file ingestion.
