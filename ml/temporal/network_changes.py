from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any

def parse_edge_timestamp(ts_val: Any) -> datetime:
    if not ts_val:
        return datetime.now()
    try:
        return datetime.fromisoformat(str(ts_val))
    except Exception:
        return datetime.now()

def track_network_evolution(graph_data: Dict[str, Any], num_slices: int = 3) -> List[Dict[str, Any]]:
    """
    Segments edge interactions into chronological time slices to measure network evolution.
    """
    edges = graph_data.get("edges", [])
    if not edges:
        return []

    parsed_edges = [(parse_edge_timestamp(e.get("timestamp")), e) for e in edges]
    parsed_edges.sort(key=lambda x: x[0])

    min_time = parsed_edges[0][0]
    max_time = parsed_edges[-1][0]
    total_delta = (max_time - min_time) or timedelta(seconds=1)

    slice_duration = total_delta / max(1, num_slices)
    slices = []

    for i in range(num_slices):
        slice_start = min_time + (slice_duration * i)
        slice_end = slice_start + slice_duration
        if i == num_slices - 1:
            slice_end = max_time + timedelta(seconds=1)

        slice_edges = [e for ts, e in parsed_edges if slice_start <= ts < slice_end]
        active_nodes = set()
        for e in slice_edges:
            if e.get("source"): active_nodes.add(e["source"])
            if e.get("target"): active_nodes.add(e["target"])

        slices.append({
            "slice_index": i + 1,
            "start_time": slice_start.isoformat(),
            "end_time": slice_end.isoformat(),
            "active_nodes_count": len(active_nodes),
            "edge_count": len(slice_edges)
        })

    return slices

def detect_new_connections(graph_data: Dict[str, Any], cutoff_iso: str = None) -> List[Dict[str, Any]]:
    """
    Identifies newly established relationships after a given timestamp.
    """
    edges = graph_data.get("edges", [])
    if not edges:
        return []

    if cutoff_iso:
        try:
            cutoff_dt = datetime.fromisoformat(cutoff_iso)
        except Exception:
            cutoff_dt = datetime.now() - timedelta(days=7)
    else:
        parsed_ts = [parse_edge_timestamp(e.get("timestamp")) for e in edges]
        parsed_ts.sort()
        cutoff_dt = parsed_ts[-1] - timedelta(days=7)

    new_edges = []
    for edge in edges:
        ts = parse_edge_timestamp(edge.get("timestamp"))
        if ts >= cutoff_dt:
            new_edges.append({
                "edge_id": edge.get("id"),
                "source": edge.get("source"),
                "target": edge.get("target"),
                "type": edge.get("type"),
                "timestamp": ts.isoformat()
            })

    return new_edges
