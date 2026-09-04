# DATABASE_SCHEMA.md

Last verified: 2026-09-04
Source of truth for schemas below: [`backend/app/audit/logger.py`](file:///d:/SIH2026/backend/app/audit/logger.py), [`backend/app/main.py`](file:///d:/SIH2026/backend/app/main.py), [`backend/app/ingestion/resolver.py`](file:///d:/SIH2026/backend/app/ingestion/resolver.py)

> [!NOTE]
> Neo4j graph node labels, properties, and relationship types are documented separately in [`GRAPH_SCHEMA.md`](file:///d:/SIH2026/GRAPH_SCHEMA.md). This document covers relational (PostgreSQL) data structures and active JSON storage schemas.

## Tables that exist and are used by running code
**Zero PostgreSQL SQL tables currently exist in active code.**

`storage/postgres/schema.sql` (2 lines) and `storage/postgres/seed.sql` (2 lines) are empty comment stubs. `backend/app/database/postgres.py` is a 6-line stub. No ORM models (SQLAlchemy/SQLModel) or raw SQL `CREATE TABLE` statements exist in the repository.

However, the running backend uses flat JSON files with structured data shapes to handle operational persistence. Their exact schemas defined in code are:

### 1. `ingestion_audit.json` Schema
Defined in [`backend/app/audit/logger.py:L28-L44`](file:///d:/SIH2026/backend/app/audit/logger.py#L28-L44). Appended to by `log_ingestion()`, read by `GET /api/ingestion-audit` in [`backend/app/main.py`](file:///d:/SIH2026/backend/app/main.py#L158).

| Field Name | Type | Description |
|---|---|---|
| `timestamp` | string (ISO 8601 UTC) | Time of ingestion event (e.g. `2026-09-01T19:24:02.080558Z`) |
| `file_name` | string | Originating filename (e.g. `FIR_001_Faisal_Khan.pdf`) |
| `source_label` | string | Ingestion source identifier (e.g. `investigator_upload`) |
| `case_id` | string \| null | Associated case ID (e.g. `CASE-102`) |
| `status` | string | Ingestion status (`"success"` \| `"error"`) |
| `message` | string | Detail message summary of extracted entities and shape |
| `entities_count` | integer | Number of entities extracted |
| `new_nodes` | integer | Number of new non-duplicate nodes created |

### 2. `filtered_edges.json` Schema
Defined in [`backend/app/audit/logger.py:L47-L64`](file:///d:/SIH2026/backend/app/audit/logger.py#L47-L64). Appended to by `log_filtered_edge()`, read by `GET /api/filtered-edges` in [`backend/app/main.py`](file:///d:/SIH2026/backend/app/main.py#L178).

| Field Name | Type | Description |
|---|---|---|
| `timestamp` | string (ISO 8601 UTC) | Time edge was filtered |
| `reason` | string | Reason code (e.g. `"self_loop"`, `"phone_conflict"`) |
| `source_doc` | string | Originating filename |
| `edge` | object | Dictionary containing edge source, target, and relationship type |

### 3. `entity_registry.json` Schema
Managed in [`backend/app/ingestion/resolver.py:L678-L694`](file:///d:/SIH2026/backend/app/ingestion/resolver.py#L678-L694), read by `GET /api/needs-review` and `GET /api/review-queue` in [`backend/app/main.py`](file:///d:/SIH2026/backend/app/main.py#L168-L210).

| Top-Level Key | Type | Description |
|---|---|---|
| `entities` | object | Map of resolved entity IDs to entity objects (`id`, `type`, `value`, `confidence`, `aliases`, `source_files`, `risk_color`, `status`, `historical_firs`) |
| `needs_review` | array of objects | Pending ambiguous identity matches requiring investigator decision |

### 4. `ReviewAction` Pydantic Model
Defined in [`backend/app/main.py:L214`](file:///d:/SIH2026/backend/app/main.py#L214). Used by `POST /api/review-queue/{review_id}/resolve`.

| Field Name | Type | Description |
|---|---|---|
| `action` | string | Resolution choice (`"merge"` \| `"reject"` \| `"skip"`) |

## Tables that exist in code but are never queried
**None.** There are no dormant SQL tables or ORM model definitions in the codebase today.

## Schema implied but not yet built
The following database structures are implied by folder layout, API stubs, or documentation, but **no SQL table or ORM model definition exists in code yet**:

- **`users` / `user_roles`**: Implied by `backend/app/users/` and `backend/app/auth/` stubs. Fields TBD — define during authentication layer implementation.
- **`cases`**: Implied by `backend/app/cases/` stubs. Fields TBD — define during case management implementation.
- **`evidence` / `evidence_files`**: Implied by `backend/app/evidence/` stubs. Fields TBD — define during evidence storage implementation.
- **`audit_logs` (SQL)**: Currently implemented as flat JSON file `data/ingestion_audit.json`. Migration to PostgreSQL SQL table is planned for a future phase.

## Naming conventions observed
Across all active code, JSON storage files, and Pydantic models, the following conventions are consistently followed:

- **Field / Attribute Names**: Strictly `snake_case` (e.g., `file_name`, `source_label`, `case_id`, `entities_count`, `new_nodes`, `source_doc`, `historical_firs`).
- **Entity Primary Keys**: Prefix-based string identifiers formatted as `<entity_type>:<hash>` (e.g., `person:a7ca11a0`, `phone:f3a47ce5`, `vehicle:b12c34d5`).
- **Case Identifiers**: String identifiers formatted as `CASE-<number>` (e.g., `CASE-102`).
- **Timestamp Format**: ISO 8601 strings in UTC with trailing `Z` (e.g., `datetime.utcnow().isoformat() + "Z"` -> `2026-09-01T19:24:02.080558Z`).
