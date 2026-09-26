# VERITAS Architectural & Data Flow Diagrams

This folder contains the complete diagram visual suite for **VERITAS**, available both as interactive rendered **Mermaid** diagrams and static PNG images.

---

## 1. Interactive Mermaid Diagrams

| Diagram Title | Description | Link / File |
|---|---|---|
| **System Architecture Topology** | High-level presentation, application, and database layer topology | [system-architecture.md](system-architecture.md) |
| **7-Stage Data Pipeline & Sequence** | Step-by-step evidence ingestion flow and WebSocket sequence | [data-flow-pipeline.md](data-flow-pipeline.md) |
| **Neo4j Graph Database Ontology** | Node labels, properties, and relationship types | [neo4j-schema.md](../database/neo4j-schema.md#0-graph-ontology-diagram-mermaid) |
| **Multi-Signal Entity Resolution** | Phonetic & fuzzy candidate matching flow | [entity-resolution.md](../ai/entity-resolution.md#implementation-architecture) |
| **Cryptographic Merkle Tree Structure** | SHA-256 evidence file checksums & Merkle Root tree | [evidence-integrity.md](../blockchain/evidence-integrity.md#cryptographic-architecture) |
| **Authorization & RBAC/ABAC Flow** | Security decision tree for roles and case assignments | [access-control.md](../security/access-control.md#0-authorization-decision-flowchart-mermaid) |
| **2-Stage Anomaly Detection Engine** | Rule engine and Isolation Forest ML pipeline | [anomaly-detection.md](../ai/anomaly-detection.md#engine-implementation) |

---

## 2. Static Diagram Image Assets

| Diagram Name | Image File | Description |
|---|---|---|
| **System Architecture** | ![Architecture Diagram](architecture.png) | End-to-end system component topology |
| **Data Flow Pipeline** | ![Data Flow Diagram](data-flow.png) | Multilingual extraction & resolution pipeline |
| **Deployment Topology** | ![Deployment Diagram](deployment.png) | Cloud & local Docker infrastructure |
| **Knowledge Graph Schema** | ![Knowledge Graph Diagram](knowledge-graph.png) | Entity relationships & document provenance |
