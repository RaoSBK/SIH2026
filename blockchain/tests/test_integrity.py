import os
import pytest
from blockchain.hashing.sha256 import compute_bytes_sha256, compute_str_sha256
from blockchain.hashing.merkle_tree import MerkleTree
from blockchain.verification.verify_hash import verify_bytes_hash
from blockchain.verification.verify_merkle import verify_merkle_proof, verify_evidence_chain
from blockchain.client.fabric_client import BlockchainIntegrityClient

def test_sha256_hashing():
    hash1 = compute_str_sha256("test_evidence_content")
    assert len(hash1) == 64
    assert verify_bytes_hash(b"test_evidence_content", hash1) is True

def test_merkle_tree():
    items = ["item_1", "item_2", "item_3", "item_4"]
    tree = MerkleTree(items)
    root = tree.get_root_hash()
    assert len(root) == 64

    # Proof verification
    leaf_hash = compute_str_sha256("item_1")
    proof = tree.get_proof(leaf_hash)
    assert len(proof) > 0
    assert verify_merkle_proof(leaf_hash, proof, root) is True

def test_evidence_chain_verification():
    items = ["doc_a", "doc_b", "doc_c"]
    tree = MerkleTree(items)
    root = tree.get_root_hash()

    chain_res = verify_evidence_chain(items, root)
    assert chain_res["valid"] is True

def test_blockchain_integrity_client(tmp_path):
    ledger_file = str(tmp_path / "test_ledger.json")
    client = BlockchainIntegrityClient(ledger_path=ledger_file)

    rec = client.register_evidence(file_name="FIR_001.txt", case_id="CASE-99", file_bytes=b"sample fir content")
    assert rec["file_sha256"] is not None
    assert rec["merkle_root"] is not None

    integrity = client.get_case_integrity("CASE-99")
    assert integrity["evidence_count"] == 1
    assert integrity["merkle_root"] == rec["merkle_root"]

    verification = client.verify_file("FIR_001.txt", rec["file_sha256"], "CASE-99")
    assert verification["verified"] is True
