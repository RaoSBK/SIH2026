import hashlib

def compute_bytes_sha256(data: bytes) -> str:
    """Computes SHA-256 hex digest of a bytes buffer."""
    if not data:
        return hashlib.sha256(b"").hexdigest()
    return hashlib.sha256(data).hexdigest()

def compute_str_sha256(text: str) -> str:
    """Computes SHA-256 hex digest of a string."""
    if not text:
        return hashlib.sha256(b"").hexdigest()
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def compute_file_sha256(file_path: str) -> str:
    """
    Computes SHA-256 hex digest of a file in 64KB chunks to efficiently handle large evidence files.
    """
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()
