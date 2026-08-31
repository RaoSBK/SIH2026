import json
import random
from datetime import datetime, timedelta
import os

def get_workspace_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current:
        if os.path.exists(os.path.join(current, "docker-compose.yml")) or os.path.exists(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return r"d:\SIH2026"

def generate_mock_graph(output_dir):
    """
    Generates a synthetic graph of entities, transactions, and communications.
    Seeds specific anomalies for testing the detection engine.
    """
    nodes = []
    edges = []
    
    # 1. Generate normal baseline (50 people)
    for i in range(1, 51):
        nodes.append({
            "id": f"PERSON_{str(i).zfill(3)}",
            "type": "PERSON",
            "name": f"Subject {i}"
        })
        
    start_date = datetime.now() - timedelta(days=30)
    
    # Generate normal transactions & calls
    for _ in range(300):
        sender = random.choice(nodes)["id"]
        receiver = random.choice([n["id"] for n in nodes if n["id"] != sender])
        
        edge_type = random.choice(["TRANSACTION", "CALL"])
        date = start_date + timedelta(days=random.randint(0, 20), hours=random.randint(0, 23))
        
        if edge_type == "TRANSACTION":
            edges.append({
                "id": f"TX-{random.randint(1000, 9999)}",
                "source": sender,
                "target": receiver,
                "type": "TRANSACTION",
                "timestamp": date.isoformat(),
                "amount": random.randint(500, 5000)
            })
        else:
            edges.append({
                "id": f"CALL-{random.randint(1000, 9999)}",
                "source": sender,
                "target": receiver,
                "type": "CALL",
                "timestamp": date.isoformat(),
                "duration": random.randint(10, 300)
            })

    # 2. Seed Anomaly 1: Transaction Spike (PERSON_042)
    # Give PERSON_042 a massive spike in transactions in the last 7 days
    spike_date = datetime.now() - timedelta(days=3)
    for _ in range(10):
        edges.append({
            "id": f"TX-ANOM1-{random.randint(1000, 9999)}",
            "source": "PERSON_042",
            "target": random.choice(nodes)["id"],
            "type": "TRANSACTION",
            "timestamp": (spike_date + timedelta(hours=random.randint(1, 48))).isoformat(),
            "amount": random.randint(50000, 100000) # Huge amounts
        })

    # 3. Seed Anomaly 2: Communication Spike (PERSON_015)
    spike_date2 = datetime.now() - timedelta(days=2)
    for _ in range(25): # Sudden burst of calls
        edges.append({
            "id": f"CALL-ANOM2-{random.randint(1000, 9999)}",
            "source": "PERSON_015",
            "target": random.choice(nodes)["id"],
            "type": "CALL",
            "timestamp": (spike_date2 + timedelta(minutes=random.randint(1, 120))).isoformat(),
            "duration": random.randint(10, 60)
        })

    # 4. Seed Anomaly 3: Bridge Node (PERSON_030 connects two isolated groups)
    bridge_date = datetime.now() - timedelta(days=1)
    for target in ["PERSON_002", "PERSON_004", "PERSON_046", "PERSON_049"]:
        edges.append({
            "id": f"CALL-ANOM3-{random.randint(1000, 9999)}",
            "source": "PERSON_030",
            "target": target,
            "type": "CALL",
            "timestamp": bridge_date.isoformat(),
            "duration": 300
        })

    graph_data = {
        "nodes": nodes,
        "edges": edges
    }
    
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "mock_graph.json")
    with open(out_path, "w") as f:
        json.dump(graph_data, f, indent=2)
        
    print(f"Generated mock graph with {len(nodes)} nodes and {len(edges)} edges at {out_path}")
    print("Seeded anomalies: PERSON_042 (Tx Spike), PERSON_015 (Call Spike), PERSON_030 (Bridge Node)")

if __name__ == "__main__":
    workspace_root = get_workspace_root()
    default_dir = os.path.join(workspace_root, "data")
    generate_mock_graph(default_dir)
