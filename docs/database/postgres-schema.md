# PostgreSQL Database & Relational Storage Schema

VERITAS uses PostgreSQL (or Supabase in cloud deployments) for relational state management (Users, Cases, Evidence Metadata) alongside structured JSON audit logs.

Source Code: [`backend/app/database/postgres.py`](file:///d:/SIH2026/backend/app/database/postgres.py), [`backend/app/users/models.py`](file:///d:/SIH2026/backend/app/users/models.py), [`backend/app/cases/models.py`](file:///d:/SIH2026/backend/app/cases/models.py), [`backend/app/evidence/models.py`](file:///d:/SIH2026/backend/app/evidence/models.py)

---

## 1. Relational SQL Tables

### `users` Table
Stores investigator and system user accounts.

| Column Name | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | Primary Key, Default: `uuid4()` | Unique user identifier |
| `username` | `VARCHAR(100)` | Unique, Not Null | Login username (e.g. `rao.a`) |
| `hashed_password` | `VARCHAR(255)` | Not Null | bcrypt hashed password digest |
| `full_name` | `VARCHAR(255)` | Not Null | Full display name (e.g. `Inspector Arjun Rao`) |
| `role` | `VARCHAR(50)` | Not Null, Default: `'investigator'` | System role (`investigator`, `supervisor`, `system_admin`) |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Default: `now()` | User creation timestamp |

### `cases` Table
Stores investigation case metadata.

| Column Name | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | Primary Key, Default: `uuid4()` | Internal database UUID |
| `case_id` | `VARCHAR(100)` | Unique, Not Null | External case reference (e.g. `CASE-102`) |
| `title` | `VARCHAR(255)` | Not Null | Case title (e.g. `Operation Crescent`) |
| `description` | `TEXT` | Nullable | Case summary narrative |
| `status` | `VARCHAR(50)` | Default: `'active'` | Case status (`active`, `archived`, `closed`) |
| `created_by` | `UUID` | Foreign Key (`users.id`) | Case creator user ID |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Default: `now()` | Case creation timestamp |

### `case_assignments` Table
Maps investigators to assigned cases (ABAC access control).

| Column Name | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | Primary Key | Assignment record ID |
| `case_id` | `VARCHAR(100)` | Foreign Key (`cases.case_id`) | Target case reference |
| `user_id` | `UUID` | Foreign Key (`users.id`) | Assigned investigator user ID |
| `assigned_at` | `TIMESTAMP WITH TIME ZONE` | Default: `now()` | Assignment timestamp |

### `evidence` Table
Tracks uploaded evidence document files.

| Column Name | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | Primary Key | Internal UUID |
| `evidence_id` | `VARCHAR(100)` | Unique, Not Null | External evidence reference (e.g. `EV-E3B0C442`) |
| `case_id` | `VARCHAR(100)` | Foreign Key (`cases.case_id`) | Associated case ID |
| `file_name` | `VARCHAR(255)` | Not Null | Original filename |
| `file_path` | `VARCHAR(500)` | Not Null | File path in storage / Supabase bucket |
| `file_sha256` | `VARCHAR(64)` | Not Null | Cryptographic SHA-256 hash |
| `uploaded_by` | `UUID` | Foreign Key (`users.id`) | Uploader user ID |
| `uploaded_at` | `TIMESTAMP WITH TIME ZONE` | Default: `now()` | Upload timestamp |

---

## 2. Structured JSON Files (Local Data Layer)

In addition to SQL tables, operational state for audit logs and review queues is managed via flat JSON files in `data/`:

1. **`data/ingestion_audit.json`**: Stores ingestion audit events (`timestamp`, `file_name`, `source_label`, `case_id`, `status`, `entities_count`, `new_nodes`).
2. **`data/entity_registry.json`**: Stores resolved entity registries and pending disambiguation review items (`needs_review` list).
3. **`data/evidence_ledger.json`**: Cryptographic evidence ledger storing SHA-256 checksums and per-case Merkle Root hashes.
4. **`data/anomaly_alerts.json`**: Persisted rule-based and Isolation Forest ML anomaly detection alerts.
