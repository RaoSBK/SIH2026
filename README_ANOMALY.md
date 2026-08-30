# CIAS Anomaly Detection Module

This module identifies unusual patterns in the CIAS Knowledge Graph. It does not classify guilt, but generates "Analytical Signals" for investigators to review.

## Architecture

The anomaly detection is broken into two stages:

### Stage 1: Rule-Based Engine (`anomaly_rules.py`)
Provides deterministic, explainable triggers based on domain heuristics:
- **Transaction Spike**: Flags when a node's transaction volume in the last 7 days exceeds 3x their historical baseline.
- **Communication Spike**: Flags when call frequency suddenly spikes by >5x.
- **Bridge Node**: Flags when an entity rapidly connects to multiple new entities that have zero overlap with their historical neighborhood (connecting isolated communities).

### Stage 2: ML-Based Scoring (`anomaly_ml.py`)
Uses `scikit-learn`'s **Isolation Forest** algorithm on behavioral features extracted from the graph (Out-degree, Total Volume, Total Transactions, Call Duration).
- The model computes an anomaly score for each node.
- Highly anomalous nodes trigger an alert. The module calculates the z-score of the node's features to provide a plain-English explanation of *why* the ML model flagged it (e.g., "Total transaction volume is abnormally high").

## Output Format

All alerts strictly follow a transparent JSON schema:

```json
{
  "alert_id": "ANOM-e1c5049b",
  "entity_id": "PERSON_042",
  "signal_type": "Analytical Signal",
  "reason": "Transaction volume increased 320% over past 7 days compared to baseline.",
  "method": "rule:transaction_spike",
  "confidence": 0.85,
  "evidence": ["TX-ANOM1-4561", "TX-ANOM1-2314"]
}
```

## Running the Tests

A synthetic generator is included that builds a mock graph and intentionally seeds anomalies (like PERSON_042 having a transaction spike).

1. Ensure dependencies are installed: `pip install scikit-learn`
2. Run the test pipeline:
```bash
python scripts/test_anomalies.py
```
This generates `data/mock_graph.json` and outputs the final alerts to `data/anomaly_alerts.json`.
