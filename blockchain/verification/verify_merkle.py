import hashlib
from typing import List, Dict, Any

def verify_merkle_proof(leaf_hash: str, proof: List[Dict[str, str]], expected_root: str) -> bool:
    """
    Verifies a Merkle proof path against expected_root hash.
    """
    if not leaf_hash or not expected_root:
        return False

    current = leaf_hash.lower()
    for step in proof:
        sibling = step.get("hash", "").lower()
        position = step.get("position", "right")

        if position == "right":
            combined = current + sibling
        else:
            combined = sibling + current

        current = hashlib.sha256(combined.encode('utf-8')).hexdigest()

    return current.lower() == expected_root.lower()

def verify_evidence_chain(evidence_hashes: List[str], expected_root: str) -> Dict[str, Any]:
    """
    Reconstructs Merkle root from evidence_hashes list and compares with expected_root.
    """
    from ..hashing.merkle_tree import MerkleTree
    tree = MerkleTree(evidence_hashes)
    computed_root = tree.get_root_hash()
    is_valid = (computed_root.lower() == expected_root.lower())

    return {
        "valid": is_valid,
        "computed_root": computed_root,
        "expected_root": expected_root,
        "evidence_count": len(evidence_hashes)
    }
