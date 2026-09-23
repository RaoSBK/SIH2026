# System Architecture Overview

VERITAS is an AI-powered criminal network analysis platform that ingests multi-format evidence documents, extracts criminal entities and relationships, merges duplicates via multi-signal resolution, persists knowledge graphs in Neo4j, and renders interactive D3.js visualization consoles for law enforcement investigators.

Source Code: [`ARCHITECTURE.md`](file:///d:/SIH2026/ARCHITECTURE.md), [`backend/app/main.py`](file:///d:/SIH2026/backend/app/main.py)

## System Topology & Microservices

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                              │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │ Next.js Frontend (Vercel) / HTML5 D3.js Console (Nginx :3000)  │   │
│   └────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP REST / WebSockets
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER                              │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │ FastAPI Backend Service (Python 3.12 / Uvicorn :8000)          │   │
│   │ ├── Ingestion Engine (PDF, DOCX, CSV, JSON, TXT Parsers)       │   │
│   │ ├── Multilingual spaCy NER & Regex Pattern Matcher             │   │
│   │ ├── Multi-Signal Entity Resolution & Disambiguation            │   │
│   │ ├── 2-Stage Anomaly Engine (Rule Engine + Isolation Forest)    │   │
│   │ └── Cryptographic Evidence Integrity Ledger Client             │   │
│   └────────────────────────────────────────────────────────────────┘   │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
                    ▼ Cypher Driver                  ▼ SQLAlchemy
┌──────────────────────────────────────┐ ┌───────────────────────────────┐
│           GRAPH DATABASE             │ │      RELATIONAL DATABASE      │
│                                      │ │                               │
│  Neo4j / Neo4j Aura (Bolt :7687)     │ │  PostgreSQL / Supabase        │
│  ├── Nodes: PERSON, PHONE, VEHICLE...│ │  ├── Cases, Users, Evidence   │
│  └── Provenance: :EXTRACTED_FROM     │ │  └── JSON Audit Logs          │
└──────────────────────────────────────┘ └───────────────────────────────┘
```

## Component Breakdown

1. **Frontend Presentation Console**: Single-Page Application (SPA) built with vanilla JS / Next.js and D3.js (Force-Directed Graph Engine). Provides real-time pipeline monitoring via WebSockets, interactive node inspection drawers, case management views, and entity review queues.
2. **FastAPI Application Backend**: Python 3.12 asynchronous service handling evidence parsing, NLP entity extraction, candidate resolution, graph construction, and anomaly scoring.
3. **Neo4j Graph Database**: Stores criminal entities as nodes and interactions (calls, transfers, associations) as directed edges. Includes full document provenance via `:EXTRACTED_FROM` links to `Document` nodes.
4. **PostgreSQL Relational DB / Supabase**: Manages relational metadata including user accounts, role permissions (RBAC), case assignments (ABAC), and uploaded evidence metadata.
5. **Cryptographic Ledger**: SHA-256 evidence file checksums and per-case Merkle Tree root calculation (`evidence_ledger.json`) for court-admissible evidence integrity verification.
