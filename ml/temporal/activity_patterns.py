from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any

def parse_edge_timestamp(ts_val: Any) -> datetime:
    """Safely parses timestamp value or defaults to datetime.now()."""
    if not ts_val:
        return datetime.now()
    try:
        return datetime.fromisoformat(str(ts_val))
    except Exception:
        return datetime.now()

def detect_burst_activity(graph_data: Dict[str, Any], window_days: int = 7) -> List[Dict[str, Any]]:
    """
    Identifies entities experiencing sudden activity spikes (>3x baseline) in recent time windows.
    """
    edges = graph_data.get("edges", [])
    if not edges:
        return []

    entity_edges = defaultdict(list)
    for edge in edges:
        s = edge.get("source")
        t = edge.get("target")
        ts = parse_edge_timestamp(edge.get("timestamp"))
        if s:
            entity_edges[s].append((ts, edge))
        if t:
            entity_edges[t].append((ts, edge))

    burst_alerts = []
    for eid, edge_list in entity_edges.items():
        if len(edge_list) < 4:
            continue

        edge_list.sort(key=lambda x: x[0])
        latest_time = edge_list[-1][0]
        cutoff = latest_time - timedelta(days=window_days)

        baseline = [e for e in edge_list if e[0] < cutoff]
        recent = [e for e in edge_list if e[0] >= cutoff]

        if not baseline or not recent:
            continue

        base_freq = len(baseline) / max(1, (cutoff - edge_list[0][0]).days or 1)
        recent_freq = len(recent) / float(window_days)

        if base_freq > 0 and (recent_freq / base_freq) >= 3.0:
            burst_alerts.append({
                "entity_id": eid,
                "type": "TEMPORAL_BURST",
                "reason": f"Activity frequency spiked {int((recent_freq / base_freq)*100)}% over last {window_days} days.",
                "recent_count": len(recent),
                "baseline_count": len(baseline)
            })

    return burst_alerts

def detect_off_hours_activity(graph_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Identifies interactions occurring during unusual/nighttime hours (23:00 to 05:00).
    """
    edges = graph_data.get("edges", [])
    off_hours_alerts = []

    for edge in edges:
        ts = parse_edge_timestamp(edge.get("timestamp"))
        hour = ts.hour
        if hour >= 23 or hour < 5:
            off_hours_alerts.append({
                "edge_id": edge.get("id"),
                "source": edge.get("source"),
                "target": edge.get("target"),
                "timestamp": ts.isoformat(),
                "hour": hour,
                "reason": f"Interaction occurred during off-hours ({hour:02d}:00)."
            })

    return off_hours_alerts
