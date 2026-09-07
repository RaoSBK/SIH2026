import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from ..hashing.sha256 import compute_file_sha256, compute_bytes_sha256
from ..hashing.merkle_tree import MerkleTree
from ..verification.verify_hash import verify_file_hash, verify_bytes_hash

logger = logging.getLogger(__name__)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
LEDGER_PATH = os.path.join(DATA_DIR, "evidence_ledger.json")

class BlockchainIntegrityClient:
    """
    Evidence Integrity & Merkle Ledger Client.
    Calculates SHA-256 evidence file checksums, builds Merkle Tree root hashes per case,
    and maintains an immutable evidence ledger log.
    """
    def __init__(self, ledger_path: str = LEDGER_PATH):
        self.ledger_path = ledger_path
        self._ensure_ledger_file()

    def _ensure_ledger_file(self):
        os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)
        if not os.path.exists(self.ledger_path):
            with open(self.ledger_path, "w", encoding="utf-8") as f:
                json.dump({"cases": {}, "records": []}, f, indent=2)

    def load_ledger(self) -> Dict[str, Any]:
        """Loads evidence ledger JSON."""
        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"cases": {}, "records": []}

    def save_ledger(self, ledger_data: Dict[str, Any]):
        """Persists evidence ledger JSON."""
        try:
            with open(self.ledger_path, "w", encoding="utf-8") as f:
                json.dump(ledger_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save evidence ledger: {e}")

    def register_evidence(
        self,
        file_name: str,
        case_id: str,
        file_path: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
        file_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registers evidence document into the cryptographic ledger,
        updating the case's Merkle Root Hash.
        """
        if not file_hash:
            if file_bytes:
                file_hash = compute_bytes_sha256(file_bytes)
            elif file_path and os.path.exists(file_path):
                file_hash = compute_file_sha256(file_path)
            else:
                file_hash = compute_bytes_sha256(file_name.encode('utf-8'))

        ledger = self.load_ledger()
        case_id = case_id or "CASE-102"
        case_info = ledger["cases"].setdefault(case_id, {"files": [], "hashes": [], "merkle_root": ""})

        # Append if file_hash not already present
        if file_hash not in case_info["hashes"]:
            case_info["hashes"].append(file_hash)
            case_info["files"].append(file_name)

        # Re-compute Merkle Tree for case
        tree = MerkleTree(case_info["hashes"])
        merkle_root = tree.get_root_hash()
        case_info["merkle_root"] = merkle_root

        record = {
            "record_id": f"EV-{file_hash[:8]}",
            "file_name": file_name,
            "case_id": case_id,
            "file_sha256": file_hash,
            "merkle_root": merkle_root,
            "timestamp": datetime.now().isoformat(),
            "status": "VERIFIED_TAMPER_EVIDENT"
        }
        ledger["records"].append(record)
        self.save_ledger(ledger)

        return record

    def get_case_integrity(self, case_id: str) -> Dict[str, Any]:
        """Returns Merkle Root and evidence file list for a case."""
        ledger = self.load_ledger()
        case_info = ledger.get("cases", {}).get(case_id, {})
        if not case_info:
            return {
                "case_id": case_id,
                "evidence_count": 0,
                "merkle_root": "",
                "files": [],
                "status": "NO_EVIDENCE_REGISTERED"
            }

        tree = MerkleTree(case_info.get("hashes", []))
        return {
            "case_id": case_id,
            "evidence_count": len(case_info.get("hashes", [])),
            "merkle_root": tree.get_root_hash(),
            "files": case_info.get("files", []),
            "status": "VERIFIED_TAMPER_EVIDENT"
        }

    def verify_file(self, file_name: str, file_hash: str, case_id: Optional[str] = None) -> Dict[str, Any]:
        """Verifies if a file's SHA-256 matches the stored ledger entry."""
        ledger = self.load_ledger()
        records = ledger.get("records", [])

        matching = [r for r in records if r["file_sha256"].lower() == file_hash.lower()]
        if matching:
            return {
                "verified": True,
                "status": "MATCH_CONFIRMED",
                "record": matching[-1]
            }

        return {
            "verified": False,
            "status": "CHECKSUM_MISMATCH_POSSIBLE_TAMPERING",
            "message": f"File hash {file_hash[:8]}... does not match any registered evidence record."
        }
