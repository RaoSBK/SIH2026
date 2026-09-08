import hashlib
from typing import List, Dict, Any, Optional
from .sha256 import compute_str_sha256

class MerkleTree:
    """
    Constructs a Merkle Tree from evidence hashes to generate a verifiable Merkle Root Hash.
    """
    def __init__(self, items: Optional[List[str]] = None):
        self.leaves: List[str] = []
        if items:
            for item in items:
                # If item is already 64-char hex hash, keep it; else compute sha256
                if len(item) == 64 and all(c in '0123456789abcdefABCDEF' for c in item):
                    self.leaves.append(item.lower())
                else:
                    self.leaves.append(compute_str_sha256(item))
                    
        self.layers: List[List[str]] = []
        if self.leaves:
            self.build_tree()

    def _hash_pair(self, left: str, right: str) -> str:
        combined = left + right
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()

    def build_tree(self):
        """Constructs tree layers from leaves to root."""
        if not self.leaves:
            self.layers = []
            return

        current_layer = list(self.leaves)
        self.layers = [current_layer]

        while len(current_layer) > 1:
            next_layer = []
            for i in range(0, len(current_layer), 2):
                left = current_layer[i]
                right = current_layer[i+1] if i + 1 < len(current_layer) else left
                parent = self._hash_pair(left, right)
                next_layer.append(parent)
            self.layers.append(next_layer)
            current_layer = next_layer

    def get_root_hash(self) -> str:
        """Returns the Merkle Root Hash of the tree."""
        if not self.layers or not self.layers[-1]:
            return hashlib.sha256(b"").hexdigest()
        return self.layers[-1][0]

    def get_proof(self, target_leaf: str) -> List[Dict[str, str]]:
        """
        Generates Merkle audit proof path for a specific leaf hash.
        
        Returns:
            list: [{"position": "right"/"left", "hash": "..."}]
        """
        target = target_leaf.lower()
        if not self.layers or target not in self.layers[0]:
            return []

        idx = self.layers[0].index(target)
        proof = []

        for layer in self.layers[:-1]:
            is_right = (idx % 2 == 1)
            pair_idx = idx - 1 if is_right else idx + 1

            if pair_idx < len(layer):
                sibling_hash = layer[pair_idx]
                position = "left" if is_right else "right"
                proof.append({"position": position, "hash": sibling_hash})

            idx = idx // 2

        return proof
