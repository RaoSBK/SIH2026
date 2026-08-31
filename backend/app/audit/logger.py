import os
import json
from datetime import datetime

AUDIT_LOG_FILE = os.path.join(os.path.dirname(__file__), "../../../data/ingestion_audit.json")

def log_ingestion(file_name: str, source_label: str, case_id: str, status: str, message: str, entities_count: int = 0, new_nodes: int = 0):
    """
    Logs every ingestion attempt (success or failure) to a JSON file.
    In Phase 2, this will be migrated to the PostgreSQL database.
    """
    os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
    
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "file_name": file_name,
        "source_label": source_label,
        "case_id": case_id,
        "status": status,
        "message": message,
        "entities_count": entities_count,
        "new_nodes": new_nodes
    }
    
    logs = []
    if os.path.exists(AUDIT_LOG_FILE):
        try:
            with open(AUDIT_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except Exception:
            pass
            
    logs.append(log_entry)
    
    try:
        with open(AUDIT_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        print(f"Failed to write to audit log: {e}")
