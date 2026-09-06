# DECISIONS.md

Append-only. Newest entries at the top. Never edit or delete a past entry — if a decision is later reversed, add a NEW entry that supersedes it and links back.

---

## 2026-09-06 — Addition of Document Relevance Validation Gate Before Graph Formation
**Decision:** Implemented `backend/app/ingestion/relevance.py` and wired `assess_relevance()` into `backend/app/ingestion/service.py` before NER extraction. Documents with insufficient domain signals (regex pattern matches or domain keywords) are rejected with `status: "rejected_low_relevance"` and bypassed before NER and graph insertion.
**Why:** Unfiltered text (e.g. food menus, receipts) was generating false-positive entities ("Puri", "Biscuits Chick") due to custom NER model limitations. Fast heuristic gating prevents non-investigative content from reaching graph generation.
**Known Limitation:** Heuristic gate using named threshold constants (`MIN_REGEX_MATCHES=1`, `MIN_DOMAIN_KEYWORDS=2`), not a trained classifier. Should be re-evaluated as more real-world document samples are collected.
**Affected areas:** `backend/app/ingestion/relevance.py`, `backend/app/ingestion/service.py`, `backend/app/main.py`, `frontend/index.html`, `DECISIONS.md`, `PROJECT_CONTEXT.md`
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
