# -*- coding: utf-8 -*-

import os

STORAGE_BASE = "storage/object-storage"

def save_file(file_bytes: bytes, case_id: str, file_name: str) -> str:
    """
    Writes to storage/object-storage/{case_id}/{file_name}, returns the path.
    Swap this function's body for a MinIO/S3 client later — callers never change.
    """
    directory = os.path.join(STORAGE_BASE, case_id)
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, file_name)
    with open(path, "wb") as f:
        f.write(file_bytes)
    return path

def get_file(storage_path: str) -> bytes:
    with open(storage_path, "rb") as f:
        return f.read()
