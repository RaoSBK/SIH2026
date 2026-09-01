import os
import json
from datetime import datetime

AUDIT_LOG_FILE    = os.path.join(os.path.dirname(__file__), "../../../data/ingestion_audit.json")
FILTERED_EDGE_LOG = os.path.join(os.path.dirname(__file__), "../../../data/filtered_edges.json")
NER_BORDERLINE_LOG = os.path.join(os.path.dirname(__file__), "../../../data/ner_borderline_log.json")


def _append_to_json_file(path: str, entry: dict) -> None:
    """Thread-safe append to a JSON array file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    records = []
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                records = json.load(f)
        except Exception:
            pass
    records.append(entry)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[audit] Failed to write {path}: {e}")


def log_ingestion(file_name: str, source_label: str, case_id: str, status: str,
                  message: str, entities_count: int = 0, new_nodes: int = 0):
    """
    Logs every ingestion attempt (success or failure) to a JSON file.
    In Phase 2, this will be migrated to the PostgreSQL database.
    """
    entry = {
        "timestamp":      datetime.utcnow().isoformat() + "Z",
        "file_name":      file_name,
        "source_label":   source_label,
        "case_id":        case_id,
        "status":         status,
        "message":        message,
        "entities_count": entities_count,
        "new_nodes":      new_nodes,
    }
    _append_to_json_file(AUDIT_LOG_FILE, entry)


def log_filtered_edge(edge: dict, reason: str, source_doc: str) -> None:
    """
    Audit trail for any edge that is removed from the graph (self-loops,
    phone conflicts, etc.).  Nothing is silently deleted — supervisors can
    query /api/filtered-edges to review all dropped edges and the reason.

    Args:
        edge:       The full relationship dict that was filtered out.
        reason:     Human-readable reason code, e.g. "self_loop", "phone_conflict".
        source_doc: Originating document filename for provenance.
    """
    entry = {
        "timestamp":  datetime.utcnow().isoformat() + "Z",
        "reason":     reason,
        "source_doc": source_doc,
        "edge":       edge,
    }
    _append_to_json_file(FILTERED_EDGE_LOG, entry)


def log_ner_borderline(entity_value: str, verdict: str, score: float,
                       source_doc: str, context: str = "") -> None:
    """
    Records every borderline NER accept/reject decision (e.g., stoplist hits,
    low-confidence name matches) so the stoplist can be tuned against real
    traffic rather than just the sample documents.

    Args:
        entity_value: The raw text that was evaluated (e.g., "Officer").
        verdict:      "accepted" | "rejected".
        score:        Confidence or similarity score at decision time.
        source_doc:   Originating document filename.
        context:      Optional surrounding sentence for human review.
    """
    entry = {
        "timestamp":    datetime.utcnow().isoformat() + "Z",
        "entity_value": entity_value,
        "verdict":      verdict,
        "score":        score,
        "source_doc":   source_doc,
        "context":      context,
    }
    _append_to_json_file(NER_BORDERLINE_LOG, entry)
