# Visual Diagrams: System Architecture

This file contains Mermaid diagram definitions and references to static architecture diagrams stored in `docs/diagrams/`.

## 1. System Topology Flowchart (Mermaid)

```mermaid
flowchart TD
    subgraph Presentation ["Presentation Layer"]
        UI["Next.js Frontend / HTML5 D3 Console"]
        GraphUI["D3.js Force Graph Visualizer"]
        ReviewUI["Disambiguation Review Queue"]
    end

    subgraph Application ["Application Layer (FastAPI Backend)"]
        API["FastAPI Router (/api)"]
        Parser["Document Parsers (PDF, DOCX, CSV, JSON, TXT)"]
        NER["spaCy NER & Pattern Extractor"]
        ER["Entity Resolver & Disambiguation Engine"]
        Anomaly["2-Stage Anomaly Engine (Rules + ML)"]
        LedgerClient["Cryptographic Evidence Ledger Client"]
    end

    subgraph Storage ["Database & Storage Layer"]
        Neo4j[("Neo4j Aura Graph Database")]
        Postgres[("PostgreSQL / Supabase DB")]
        Ledger[("Evidence Ledger JSON (SHA-256 / Merkle)")]
    end

    UI --> API
    API --> Parser
    Parser --> NER
    NER --> ER
    ER --> Neo4j
    ER --> Anomaly
    API --> Postgres
    API --> LedgerClient
    LedgerClient --> Ledger
```

## 2. Static Diagram References

- **Architecture Diagram Image**: ![Architecture Diagram](architecture.png)
- **Deployment Topology Image**: ![Deployment Diagram](deployment.png)
