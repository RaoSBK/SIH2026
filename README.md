# VERITAS — AI-Powered Criminal Network Analysis

> Turn unstructured case evidence into clear, actionable criminal network graphs in seconds.

**[Full Documentation](docs/README.md)**


## Problem Statement (SIH26189)
Investigating criminal networks requires sifting through hundreds of unstructured evidence files like FIRs, call records, and bank transactions. Manual analysis across isolated documents is slow and error-prone, causing investigators to miss hidden links and critical network leads. VERITAS automates this process for Problem Statement SIH26189 (Ministry of Home Affairs).

## What VERITAS Does
- **Multi-Format Evidence Ingestion**: Parses FIR narratives, CDR logs, bank statements, and case files (PDF, DOCX, CSV, JSON, TXT).
- **Automated Entity & Relationship Extraction**: Identifies suspects, phone numbers, vehicles, locations, and events using NLP and pattern matching.
- **Multi-Signal Entity Disambiguation**: Merges duplicate records like phone aliases and phonetic name variants, placing ambiguous matches in a review queue.
- **Interactive Knowledge Graph**: Builds a unified connection network with complete evidence provenance for every node and link.
- **Suspicious Subnetwork Flagging**: Automatically highlights high-risk hubs and central co-conspirators for investigator focus.

## How It Works
```
Evidence Files (PDF/DOCX/CSV/TXT/JSON)
  └─► Entity & Relation Extraction (NLP & Rules)
        └─► Entity Resolution & Review Queue (Fuzzy/Phonetic Merging)
              └─► Knowledge Graph Engine (Neo4j & Risk Scoring)
                    └─► Investigator Console (D3.js Force Graph & Audit Trace)
```

## Tech Stack
| Layer | Technology |
|---|---|
| **Frontend** | Vanilla JS, HTML5, CSS3, D3.js (Force-Directed Graph), Lucide Icons |
| **Backend** | Python 3.12, FastAPI, Uvicorn, Pydantic, SQLAlchemy |
| **NLP & Entity Resolution** | spaCy, RapidFuzz, PyMuPDF, python-docx, pandas, Jaro-Winkler clustering (`cias_er`) |
| **Graph & Storage** | Neo4j (Cypher), PostgreSQL, JSON Audit Logs |
| **Infrastructure** | Docker, Docker Compose, Nginx |

## Try It
- **Live Demo**: `[INSERT_VERCEL_DEPLOYMENT_URL]` *(Update with your active Vercel link)*
- **Test Credentials**: Open access / `investigator@veritas.gov.in` (`veritas2026`)
- **System Diagrams**:
  - ![Architecture Diagram](docs/diagrams/architecture.png)
  - ![Data Flow Diagram](docs/diagrams/data-flow.png)

## Quick Setup (Local Docker)
```bash
# 1. Clone the repository
git clone https://github.com/RaoSBK/SIH2026.git
cd SIH2026

# 2. Launch full stack via Docker Compose
docker-compose up --build -d
```
Access the local environment:
- **Frontend Console**: `http://localhost:3000`
- **Backend API Swagger**: `http://localhost:8000/docs`


## What Makes VERITAS Different
- **Cross-Source Pattern Fusion**: Merges call detail records, financial transactions, location logs, and FIR narratives into a single unified graph.
- **Confidence-Weighted Graph Resolution**: Tracks uncertainty and phonetic match confidence across entities, routing ambiguous identities to human investigators.
- **Natural-Language Investigator Queries**: Enables officers to explore suspect connections and evidence trails directly without complex database queries.

## Team & Hackathon
Built for **Smart India Hackathon (SIH) 2026** | Problem Statement **SIH26189** (Ministry of Home Affairs).
