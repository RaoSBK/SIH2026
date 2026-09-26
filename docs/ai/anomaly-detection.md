# Anomaly & Suspicious Subnetwork Detection

VERITAS employs a two-stage anomaly detection architecture to highlight high-risk nodes, suspicious financial loops, and covert criminal communication hubs.

## Engine Implementation

Source Code: [`ml/anomaly/anomaly_rules.py`](file:///d:/SIH2026/ml/anomaly/anomaly_rules.py), [`ml/anomaly/anomaly_ml.py`](file:///d:/SIH2026/ml/anomaly/anomaly_ml.py), [`backend/app/api/anomaly.py`](file:///d:/SIH2026/backend/app/api/anomaly.py)

```mermaid
flowchart TD
    GraphPayload["Incoming Graph Payload (Nodes & Edges)"] --> Stage1["Stage 1: Rule Engine (anomaly_rules.py)"]
    GraphPayload --> Stage2["Stage 2: Isolation Forest ML (anomaly_ml.py)"]

    subgraph Stage1Rules ["Deterministic Network Rules"]
        R1["Hub Detection (Degree >= 5 -> Red, >= 3 -> Orange)"]
        R2["CDR Call Frequency Bursts"]
        R3["Smurfing / Structuring Financial Loops"]
        R4["Multi-Source Implication (FIR + CDR + Bank)"]
    end

    subgraph Stage2ML ["Unsupervised Outlier Detection"]
        F1["Node Degree & In/Out Ratio"]
        F2["Transaction & Call Volume"]
        F3["Connected Component Topology"]
        F4["Multi-Evidence Source Count"]
        IsolationForest["Scikit-Learn Isolation Forest Model"]
    end

    Stage1 --> Stage1Rules
    Stage2 --> Stage2ML
    Stage2ML --> IsolationForest

    Stage1Rules --> MergeAlerts["Merge & Deduplicate Anomaly Alerts"]
    IsolationForest --> MergeAlerts

    MergeAlerts --> Persist["Save to data/anomaly_alerts.json"]
    Persist --> UIHighlight["UI Risk Styling (status: REVIEW_REQUIRED, risk_color: red/orange)"]

    style Stage1 fill:#ffcc99,stroke:#ff6600,stroke-width:1.5px
    style Stage2 fill:#99ccff,stroke:#0066cc,stroke-width:1.5px
    style UIHighlight fill:#ff9999,stroke:#cc0000,stroke-width:2px
```


## Stage 1: Rule-Based Network Engine (`anomaly_rules.py`)

The rule engine evaluates deterministic criminal network patterns:
- **High Degree / Hub Detection**: Flags entities with total connection degree $\ge 5$ (high-risk red) or $\ge 3$ (orange).
- **Rapid CDR Burst**: Flags phone numbers with unusually high call frequencies within short temporal windows.
- **Structuring / Smurfing Financial Loops**: Detects accounts engaging in split financial transactions (`TRANSFERRED_TO`) designed to evade banking thresholds.
- **Multi-Evidence Implication**: Flags entities that appear across $\ge 2$ distinct evidence document types (e.g., named in both an FIR and a CDR log).

## Stage 2: Isolation Forest ML Engine (`anomaly_ml.py`)

The ML engine constructs numerical feature vectors for each graph node:
- **Node Degree & In/Out Ratio**
- **Total Transaction / Call Volume**
- **Connected Component Size**
- **Multi-Source Evidence Count**

An **Isolation Forest** model (`scikit-learn`) scores nodes based on isolation depth. Nodes falling beyond the anomaly threshold are flagged as structural outliers.

## Persistence & UI Indicators

Anomalies are persisted to `data/anomaly_alerts.json` and served via `GET /api/anomalies` and `GET /api/cases/{case_id}/anomalies`. Flagged nodes receive:
- `status`: `"REVIEW_REQUIRED"`
- `risk_color`: `"red"` or `"orange"`
- `anomaly_reasons`: Detailed human-interpretable reasoning strings appended to the node UI drawer.
