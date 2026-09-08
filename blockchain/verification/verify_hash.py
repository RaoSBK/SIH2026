import os
from ..hashing.sha256 import compute_file_sha256, compute_bytes_sha256

def verify_file_hash(file_path: str, expected_hash: str) -> bool:
    """
    Verifies that the SHA-256 hash of a file matches expected_hash.
    """
    if not os.path.exists(file_path) or not expected_hash:
        return False
    actual_hash = compute_file_sha256(file_path)
    return actual_hash.lower() == expected_hash.strip().lower()

def verify_bytes_hash(data: bytes, expected_hash: str) -> bool:
    """
    Verifies that the SHA-256 hash of a bytes buffer matches expected_hash.
    """
    if not expected_hash:
        return False
    actual_hash = compute_bytes_sha256(data)
    return actual_hash.lower() == expected_hash.strip().lower()
