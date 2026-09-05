# DECISIONS.md

Append-only. Newest entries at the top. Never edit or delete a past entry — if a decision is later reversed, add a NEW entry that supersedes it and links back.

---

## 2026-09-05 — Case-Scoped Entity Resolution & Same-Case Automatic Matching Policy
**Decision:** Updated `EntityRegistry.all_of_type(etype, case_id)` and candidate lookups in `backend/app/ingestion/resolver.py` (`_resolve_persons`, `_resolve_locations`) to filter entity candidates by the active upload's `case_id`. Untracked `data/entity_registry.json` and `data/ingestion_audit.json` in `.gitignore` without deleting existing disk contents.
**Why:** Candidate fuzzy matching previously fetched all entities globally across all cases (`registry.all_of_type("PERSON")`), causing cross-case entity pollution where uploads in Case B merged into entities from Case A.
**Policy Note (Cross-case linking):** Automatic entity matching defaults strictly to same-case candidates. Cross-case entity linking (identifying the same individual across separate investigations) is reserved for explicit investigator review via `needs_review` actions rather than silent automatic merging.
**Affected areas:** `backend/app/ingestion/resolver.py`, `.gitignore`, `DECISIONS.md`, `PROJECT_CONTEXT.md`
**Supersedes:** N/A

---

## 2026-09-05 — Long-Term Entity Resolution Candidate Store (Phase 2 Architecture Note)
**Decision:** Documented Phase 2 design to migrate `EntityRegistry` candidate lookups from local JSON (`data/entity_registry.json`) directly into Neo4j using `case_id`-scoped Cypher queries matching the `get_case_graph` pattern (`MATCH (n)-[:EXTRACTED_FROM]->(:Document {case_id: $case_id})`).
**Why:** Replaces file-based JSON persistence with container-persistent Neo4j graph queries for candidate lookup, aligning ingestion resolution with standard graph reading patterns.
**Affected areas:** `backend/app/ingestion/resolver.py`, `ARCHITECTURE.md`, `DECISIONS.md`
**Supersedes:** N/A

---

## 2026-09-05 — Docker Container Packaging Fix for `cias_er` Package Dependency
**Decision:** Added `COPY cias_er /app/cias_er` to `backend/Dockerfile` and mounted `./cias_er:/app/cias_er` as a volume in `docker-compose.yml`.
**Why:** `backend/app/ingestion/resolver.py` imported `cias_er.matcher` and `cias_er.clustering`, but `cias_er` was omitted from the Docker build context and volume mounts, causing a `ModuleNotFoundError: No module named 'cias_er'` crash loop on backend startup.
**Affected areas:** `backend/Dockerfile`, `docker-compose.yml`, `backend/app/ingestion/resolver.py`
**Supersedes:** N/A

---

## 2026-09-04 — Creation of Project Context, Architecture, Database Schema, and Graph Schema Single Source of Truth Files
**Decision:** Audited the entire repository and generated four canonical documentation files at the repo root: `PROJECT_CONTEXT.md`, `ARCHITECTURE.md`, `DATABASE_SCHEMA.md`, and `GRAPH_SCHEMA.md`.
**Why:** Establishes explicit ground truth for all working API routes, active ingestion pipelines, container configurations, and database/Cypher schemas, preventing AI agents and contributors from guessing or hallucinating non-existent models or fields in future sessions.
**Affected areas:** `PROJECT_CONTEXT.md`, `ARCHITECTURE.md`, `DATABASE_SCHEMA.md`, `GRAPH_SCHEMA.md`, `DECISIONS.md`
**Supersedes:** N/A

---

## 2026-08-31 — Unification of Ingestion Layer & Deprecation of Standalone ML Processors
**Decision:** Established `backend/app/ingestion/` (`ner.py`, `resolver.py`, `service.py`) as the single canonical ingestion and entity resolution pipeline, dropping `ml/processor.py` from active execution.
**Why:** Inferred from commit history (`056c837`: "fix: resolve merge conflicts with main - unify build context, drop ml_processor, keep ingestion pipeline deps"). Standardized backend file uploads onto a single FastAPI execution path.
**Affected areas:** `backend/app/ingestion/`, `ml/processor.py`, `docker-compose.yml`
**Supersedes:** `2026-08-30 — Initial ML NLP and Anomaly Engine Implementation`

---

## 2026-08-31 — Project Codebase Reorganization into Categorized Modules
**Decision:** Reorganized standalone Python scripts from root/scripts into dedicated directories: NLP scripts under `ml/nlp`, anomaly detection under `ml/anomaly`, and graph generation under `graph`.
**Why:** Recorded in `memory.md`: "Reorganized Python scripts into correct respective directories (`ml/nlp`, `ml/anomaly`, `graph`) and updated connections/paths."
**Affected areas:** `ml/nlp/`, `ml/anomaly/`, `graph/`, `scripts/`
**Supersedes:** N/A

---

## 2026-08-30 — Adoption of Force-Directed Layout & Scroll-to-Zoom Graph Engine
**Decision:** Overhauled graph rendering in the investigator console using D3.js force-directed physics layout with explicit entity node styling and scroll-to-zoom controls.
**Why:** Inferred from commit history (`fd94c31`: "feat: complete graph engine overhaul with force-directed layout, explicit entity typing, and scroll-to-zoom").
**Affected areas:** `frontend/graph/graph.js`, `frontend/index.html`
**Supersedes:** `2026-08-30 — Initial Dynamic ML Graph Layout Integration`

---

## 2026-08-30 — Initial ML NLP and Anomaly Engine Implementation
**Decision:** Implemented standalone spaCy NLP extraction, OCR noise cleaning, PDF integration, and Isolation Forest anomaly models inside `ml/`.
**Why:** Inferred from commit history (`631fca0`: "feat: add CIAS NLP extraction and anomaly detection engine ML").
**Affected areas:** `ml/processor.py`, `ml/nlp/cias_nlp.py`, `ml/anomaly/anomaly_ml.py`
**Supersedes:** N/A

---

## 2026-08-29 — Abandonment of React SPA Framework in Favor of Standalone Single-Page HTML/D3 UI
**Decision:** Purged React `src/` boilerplate and switched the investigator console frontend to a single-file vanilla HTML/JS/CSS application (`frontend/index.html` and `frontend/graph/graph.js`).
**Why:** Recorded in `memory.md`: "The project initially started as a React app but was shifted to raw HTML/JS per user request. This required purging the old src directory to keep the workspace clean."
**Affected areas:** `frontend/`, `frontend/package.json`, `index.html`
**Supersedes:** N/A

---

## 2026-08-29 — Adoption of Light Theme UI Palette
**Decision:** Inverted the application's color palette in `frontend/index.html` from a dark theme to a clean light theme.
**Why:** Recorded in `memory.md`: "Inverted the application's color palette to a Light Theme."
**Affected areas:** `frontend/index.html`, `index.html`
**Supersedes:** N/A

---

## 2026-08-29 — Code File Size Constraint (~250 Lines Limit)
**Decision:** Established project-wide rule that code files must stay under ~250 lines, splitting large features into separate modules.
**Why:** Recorded in `rules.md`: "Code files must be under ~250 lines. Split features/pages into separate files."
**Affected areas:** Entire workspace
**Supersedes:** N/A
