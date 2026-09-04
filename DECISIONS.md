# DECISIONS.md

Append-only. Newest entries at the top. Never edit or delete a past entry — if a decision is later reversed, add a NEW entry that supersedes it and links back.

---

## 2026-09-04 — Integration of Neo4j Node Merging & Review Queue Graph Refactoring
**Decision:** Implemented `merge_nodes_in_neo4j` in [`backend/app/database/neo4j.py`](file:///d:/SIH2026/backend/app/database/neo4j.py) and wired it directly into `resolve_review_item()` (`POST /api/review-queue/{review_id}/resolve`) in [`backend/app/main.py`](file:///d:/SIH2026/backend/app/main.py).
**Why:** Synchronizes investigator merge decisions in the review queue UI directly with the live Neo4j graph database, combining aliases, provenance, and re-linking graph relationships.
**Affected areas:** `backend/app/database/neo4j.py`, `backend/app/main.py`, `PROJECT_CONTEXT.md`
**Supersedes:** N/A

---

## 2026-09-04 — Integration of ML OCR Noise Cleaning & Syntactic Dependency Verb Extraction into Live Ingestion Engine
**Decision:** Integrated OCR noise cleaning (`clean_ocr_noise`) and syntactic dependency tree verb extraction (`_extract_syntactic_verb`) from [`ml/processor.py`](file:///d:/SIH2026/ml/processor.py) into canonical ingestion module [`backend/app/ingestion/ner.py`](file:///d:/SIH2026/backend/app/ingestion/ner.py).
**Why:** Enhances unstructured document processing by repairing OCR artifacts before spaCy NER and dynamically discovering action verb relationships (e.g. `VISIT`, `MEET`, `TRANSFER`, `CALL`) between entities co-occurring in sentences.
**Affected areas:** `backend/app/ingestion/ner.py`, `backend/app/ingestion/service.py`, `ml/processor.py`, `PROJECT_CONTEXT.md`
**Supersedes:** N/A

---

## 2026-09-04 — Consolidation of `cias_er` Entity Resolution Algorithms into Live Ingestion Resolver
**Decision:** Consolidated Jaro-Winkler name similarity scoring (`calculate_name_score`), Token Set Ratio address matching (`calculate_address_score`), and historical FIR/risk scoring (`check_criminal_history`) from `cias_er/` into the live ingestion resolver in [`backend/app/ingestion/resolver.py`](file:///d:/SIH2026/backend/app/ingestion/resolver.py).
**Why:** Brings advanced string distance and criminal history risk profiling into the active `POST /api/process-evidence` endpoint without creating parallel pipelines or breaking strict multi-signal corroboration rules (`case_id`, shared phones/accounts).
**Affected areas:** `backend/app/ingestion/resolver.py`, `cias_er/matcher.py`, `cias_er/clustering.py`, `cias_er/pipeline.py`, `PROJECT_CONTEXT.md`
**Supersedes:** N/A

---

## 2026-09-04 — Integration of ML Isolation Forest & Rule Anomaly Detection Engine into FastAPI Backend
**Decision:** Imported `run_rule_engine` ([`ml/anomaly/anomaly_rules.py`](file:///d:/SIH2026/ml/anomaly/anomaly_rules.py)) and `run_ml_engine` ([`ml/anomaly/anomaly_ml.py`](file:///d:/SIH2026/ml/anomaly/anomaly_ml.py)) into [`backend/app/main.py`](file:///d:/SIH2026/backend/app/main.py) to replace the static connection-count heuristic in `process_evidence()` with multi-stage ML Isolation Forest scoring and rule-based anomaly detection.
**Why:** Replaced static connectivity heuristics with real ML anomaly models for transaction spikes, communication spikes, and bridge node detection, updating node risk colors (`"red"`, `"orange"`) and status flags (`"REVIEW_REQUIRED"`).
**Affected areas:** `backend/app/main.py`, `ml/anomaly/anomaly_rules.py`, `ml/anomaly/anomaly_ml.py`, `PROJECT_CONTEXT.md`
**Supersedes:** N/A

---

## 2026-09-04 — Resolution of Test Suite Regressions & Alignment of Entity Resolution Corroboration Logic
**Decision:** Updated RapidFuzz distance imports in `cias_er/matcher.py`, corrected mock patch target paths in `backend/tests/test_pipeline.py`, and refined `backend/app/ingestion/resolver.py` signal extraction to allow auto-merging on shared phone/account corroboration while preventing false auto-merges across conflicting explicit `case_id`s.
**Why:** Brought all active test suites across the repository (`backend/tests/test_pipeline.py`, `cias_er/tests/test_pipeline.py`, `ml/anomaly/tests/test_anomalies.py`, `ml/nlp/tests/test_nlp.py`) to a 100% passing state (18 passed, 0 failed).
**Affected areas:** `backend/tests/test_pipeline.py`, `cias_er/matcher.py`, `backend/app/ingestion/resolver.py`, `PROJECT_CONTEXT.md`
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
