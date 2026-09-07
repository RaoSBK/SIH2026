import os
import json
import logging
from typing import Dict, Any

from ml.nlp.ner.inference import predict_entities
from ml.anomaly.anomaly_ml import run_ml_engine
from cias_er.matcher import score_pair

logger = logging.getLogger("MLEvaluationHarness")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
EVAL_REPORT_PATH = os.path.join(DATA_DIR, "ml_evaluation_report.json")

BENCHMARK_NER_TEXTS = [
    {
        "text": "Suspect Mr. Ravi Kumar was identified near Andheri Police Station. Phone: 9876543210. Vehicle: MH12AB1234.",
        "expected_types": ["PERSON", "LOCATION", "PHONE", "VEHICLE"]
    },
    {
        "text": "Case ID CASE-102. Dr. Suresh Sharma visited Bandra Branch.",
        "expected_types": ["CASE_ID", "PERSON", "LOCATION"]
    }
]

BENCHMARK_GRAPH = {
    "nodes": [
        {"id": "n1", "type": "PERSON"},
        {"id": "n2", "type": "PERSON"},
        {"id": "n3", "type": "PERSON"},
        {"id": "n4", "type": "PERSON"}
    ],
    "edges": [
        {"id": "e1", "source": "n1", "target": "n2", "type": "TRANSACTION", "amount": 500000.0},
        {"id": "e2", "source": "n1", "target": "n3", "type": "TRANSACTION", "amount": 750000.0},
        {"id": "e3", "source": "n1", "target": "n4", "type": "CALL", "duration": 1200.0}
    ]
}

def evaluate_ner() -> Dict[str, float]:
    """Evaluates Precision, Recall, F1 for NER extraction."""
    true_positives = 0
    false_positives = 0
    false_negatives = 0

    for sample in BENCHMARK_NER_TEXTS:
        predicted = predict_entities(sample["text"])
        pred_types = [e["type"] for e in predicted]
        exp_types = sample["expected_types"]

        for pt in pred_types:
            if pt in exp_types:
                true_positives += 1
            else:
                false_positives += 1

        for et in exp_types:
            if et not in pred_types:
                false_negatives += 1

    precision = true_positives / max(1, true_positives + false_positives)
    recall = true_positives / max(1, true_positives + false_negatives)
    f1 = (2 * precision * recall) / max(1e-5, precision + recall)

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4)
    }

def evaluate_anomaly_detection() -> Dict[str, Any]:
    """Evaluates Isolation Forest Anomaly Detection outputs."""
    alerts = run_ml_engine(BENCHMARK_GRAPH)
    total_detected = len(alerts)
    anomalous_nodes = {a["entity_id"] for a in alerts}

    precision = 1.0 if "n1" in anomalous_nodes else 0.0

    return {
        "anomalies_detected": total_detected,
        "primary_outlier_identified": "n1" in anomalous_nodes,
        "precision": precision
    }

def evaluate_entity_resolution() -> Dict[str, float]:
    """Evaluates Entity Resolution matching accuracy."""
    pair_matches = [
        ({"id": "p1", "name": "Ravi Kumar", "phone": "9876543210"}, {"id": "p2", "name": "Ravee Kumar", "phone": "9876543210"}, True),
        ({"id": "p1", "name": "Ravi Kumar", "phone": "9876543210"}, {"id": "p3", "name": "Suresh Sharma", "phone": "1111111111"}, False)
    ]

    correct = 0
    for e1, e2, expected in pair_matches:
        score = score_pair(e1, e2)
        is_match = score >= 0.70
        if is_match == expected:
            correct += 1

    accuracy = correct / len(pair_matches)
    return {"accuracy": round(accuracy, 4)}

def run_evaluation() -> Dict[str, Any]:
    """Runs complete ML Evaluation Suite."""
    print("--- Running ML Evaluation Harness ---")
    ner_metrics = evaluate_ner()
    anomaly_metrics = evaluate_anomaly_detection()
    er_metrics = evaluate_entity_resolution()

    report = {
        "evaluation_timestamp": os.path.basename(EVAL_REPORT_PATH),
        "ner_evaluation": ner_metrics,
        "anomaly_detection_evaluation": anomaly_metrics,
        "entity_resolution_evaluation": er_metrics
    }

    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(EVAL_REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Successfully saved evaluation report to {EVAL_REPORT_PATH}")
    except Exception as e:
        print(f"Failed to write evaluation report: {e}")

    return report

if __name__ == "__main__":
    rep = run_evaluation()
    print(json.dumps(rep, indent=2))
