from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Any

def parse_edge_timestamp(ts_val: Any) -> datetime:
    if not ts_val:
        return datetime.now()
    try:
        return datetime.fromisoformat(str(ts_val))
    except Exception:
        return datetime.now()

def build_temporal_features(graph_data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """
    Constructs per-node temporal feature dictionaries to enrich ML anomaly models.
    
    Features:
    - burst_score: ratio of recent 7-day activity vs historical baseline.
    - off_hours_ratio: percentage of calls/tx occurring between 23:00 - 05:00.
    - active_days_span: days between first and last interaction.
    - recent_velocity: count of interactions in past 7 days.
    """
    nodes = {n["id"]: n for n in graph_data.get("nodes", [])}
    edges = graph_data.get("edges", [])

    node_timestamps = defaultdict(list)
    off_hours_counts = defaultdict(int)
    total_counts = defaultdict(int)

    for edge in edges:
        s = edge.get("source")
        t = edge.get("target")
        ts = parse_edge_timestamp(edge.get("timestamp"))

        is_off_hour = (ts.hour >= 23 or ts.hour < 5)

        for nid in (s, t):
            if nid:
                node_timestamps[nid].append(ts)
                total_counts[nid] += 1
                if is_off_hour:
                    off_hours_counts[nid] += 1

    all_node_ids = set(nodes.keys()).union(node_timestamps.keys())
    features = {}

    for nid in all_node_ids:
        ts_list = sorted(node_timestamps.get(nid, []))
        tot_cnt = float(total_counts[nid])
        off_cnt = float(off_hours_counts[nid])

        if not ts_list:
            features[nid] = {
                "burst_score": 1.0,
                "off_hours_ratio": 0.0,
                "active_days_span": 0.0,
                "recent_velocity": 0.0
            }
            continue

        latest_time = ts_list[-1]
        earliest_time = ts_list[0]
        span_days = max(1.0, (latest_time - earliest_time).days + 1.0)

        cutoff = latest_time - timedelta(days=7)
        recent_cnt = float(sum(1 for t in ts_list if t >= cutoff))
        baseline_cnt = tot_cnt - recent_cnt

        baseline_freq = baseline_cnt / max(1.0, span_days - 7.0)
        recent_freq = recent_cnt / 7.0

        burst_score = (recent_freq / baseline_freq) if baseline_freq > 0 else 1.0
        off_hours_ratio = off_cnt / tot_cnt if tot_cnt > 0 else 0.0

        features[nid] = {
            "burst_score": round(burst_score, 2),
            "off_hours_ratio": round(off_hours_ratio, 2),
            "active_days_span": float(span_days),
            "recent_velocity": float(recent_cnt)
        }

    return features
