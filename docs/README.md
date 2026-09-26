# VERITAS Documentation Index

Welcome to the official documentation for **VERITAS** (AI-Powered Criminal Network Analysis System), built for Smart India Hackathon (SIH) 2026, Problem Statement **SIH26189** (Ministry of Home Affairs).

## Documentation Structure

This repository documentation is organized into 8 core sections:

| Section | Description | Key Topics |
|---|---|---|
| [**`docs/ai/`**](ai/nlp.md) | Artificial Intelligence & Machine Learning | Entity Extraction (NER), Disambiguation & Resolution, Anomaly Detection, Graph Analytics |
| [**`docs/api/`**](api/endpoints.md) | API Specifications & Endpoints | FastAPI Route Reference, Request/Response Payload Models, OpenAPI Spec |
| [**`docs/architecture/`**](architecture/system-architecture.md) | System Architecture & Topology | Core Components, 7-Stage Pipeline, Cloud Deployment (Vercel, Render, Supabase, Neo4j Aura) |
| [**`docs/blockchain/`**](blockchain/evidence-integrity.md) | Cryptographic Evidence Integrity | SHA-256 File Checksums, Merkle Tree Root Calculation, Tamper-Evident Ledger |
| [**`docs/database/`**](database/postgres-schema.md) | Database & Storage Schemas | Relational PostgreSQL Schemas, Neo4j Graph Ontology, Cypher Query Patterns |
| [**`docs/demo/`**](demo/demo-script.md) | Evaluator Demo & Test Flows | Step-by-Step Judge Walkthrough Script, Case "Operation Crescent" Test Scenario |
| [**`docs/diagrams/`**](diagrams/README.md) | Architecture & Pipeline Diagrams | Mermaid Architecture Flowcharts, Sequence Diagrams, Visual Image References |

| [**`docs/security/`**](security/access-control.md) | Security, Auth & Access Control | Role-Based Access (RBAC), Case Access (ABAC), Evidence Hashing, PII Masking, Threat Model |

---

## 7-Stage Processing Pipeline Overview

```
 ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
 │ 1. INGEST │───►│2.NORMALIZE│───►│ 3. EXTRACT│───►│4. RESOLVE │
 └───────────┘    └───────────┘    └───────────┘    └───────────┘
                                                          │
 ┌───────────┐    ┌───────────┐    ┌───────────┐          │
 │7. EXPLAIN │◄───│6. ANALYZE │◄───│  5. GRAPH │◄─────────┘
 └───────────┘    └───────────┘    └───────────┘
```

1. **Ingest**: Ingests multi-format evidence files (FIR PDFs, CDR CSVs, Bank JSON, DOCX narratives, TXT).
2. **Normalize**: Standardizes names, phone numbers (E.164), accounts, and registration strings.
3. **Extract**: Multilingual spaCy NER and pattern matchers extract entities and relationship triples.
4. **Resolve**: Multi-signal disambiguation (Jaro-Winkler, Double Metaphone) merges duplicates and queues ambiguities.
5. **Graph**: Batched Neo4j graph construction with document provenance (`:EXTRACTED_FROM`).
6. **Analyze**: 2-stage anomaly engine (rule engine + Isolation Forest) and NetworkX analytics score subnetwork risks.
7. **Explain**: Generates evidence trail, risk indicators, and human-interpretable reasoning for investigators.
