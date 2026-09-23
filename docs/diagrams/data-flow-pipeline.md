# Visual Diagrams: 7-Stage Pipeline & Data Flow

This file contains Mermaid sequence diagrams and pipeline flowcharts for the 7-stage evidence processing engine in VERITAS.

## 1. 7-Stage Processing Pipeline Flowchart (Mermaid)

```mermaid
graph LR
    S0["0. Ingest"] --> S1["1. Normalize"]
    S1 --> S2["2. Extract"]
    S2 --> S3["3. Resolve"]
    S3 --> S4["4. Graph"]
    S4 --> S5["5. Analyze"]
    S5 --> S6["6. Explain"]
    S6 --> S7["7. Complete"]

    style S0 fill:#f9f,stroke:#333,stroke-width:1px
    style S3 fill:#bbf,stroke:#333,stroke-width:1px
    style S4 fill:#bfb,stroke:#333,stroke-width:1px
    style S5 fill:#ffb,stroke:#333,stroke-width:1px
```

## 2. Asynchronous Ingestion & WebSocket Execution Sequence (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    actor Investigator
    participant Frontend as D3.js Console UI
    participant Backend as FastAPI Backend
    participant Pipeline as Pipeline Worker
    participant Neo4j as Neo4j Database
    participant Ledger as Evidence Ledger

    Investigator->>Frontend: Select & Upload Evidence Files (PDF/CDR)
    Frontend->>Backend: POST /api/process-evidence (files, case_id)
    Backend->>Ledger: Register SHA-256 Checksum & Merkle Root
    Backend-->>Frontend: Return job_id (Status: queued)
    Frontend->>Backend: Connect WebSocket /api/pipeline/ws/{job_id}

    Backend->>Pipeline: Dispatch run_pipeline_job()
    Pipeline->>Backend: Stage 0: Ingest (Parse Files)
    Backend-->>Frontend: WS Push (Stage 0 Logs)

    Pipeline->>Backend: Stage 2: Parallel NER Extraction
    Backend-->>Frontend: WS Push (Stage 2 Logs)

    Pipeline->>Backend: Stage 3: Entity Resolution & Phonetic Matching
    Backend-->>Frontend: WS Push (Stage 3 Logs)

    Pipeline->>Neo4j: Stage 4: UNWIND Batch Write Nodes & Edges
    Pipeline->>Backend: Stage 5: Isolation Forest & Rule Anomaly Detection
    Pipeline->>Backend: Stage 6: Attach Risk Indicators & Evidence Trail

    Pipeline-->>Backend: Job Complete
    Backend-->>Frontend: WS Push (Status: completed, Full Graph Payload)
    Frontend->>Investigator: Render D3.js Force Graph with Flagged Nodes
```

## 3. Static Image References

- **Data Flow Diagram Image**: ![Data Flow Diagram](data-flow.png)
- **Knowledge Graph Diagram Image**: ![Knowledge Graph Diagram](knowledge-graph.png)
