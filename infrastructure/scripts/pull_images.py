#!/usr/bin/env python3
"""
CIAS Docker Pull Helper
Retries docker pull with exponential backoff to handle unstable connections.
Run this ONCE before docker compose up --build -d
"""
import subprocess
import time
import sys

IMAGES = [
    "postgres:15-alpine",      # small ~50MB - should be fine
    "neo4j:5.20.0-community",  # large ~500MB - needs retries
]

def pull_with_retry(image, max_retries=10, initial_wait=5):
    print(f"\n[PULL] Attempting to pull: {image}")
    for attempt in range(1, max_retries + 1):
        print(f"  Attempt {attempt}/{max_retries}...")
        result = subprocess.run(
            ["docker", "pull", image],
            capture_output=False
        )
        if result.returncode == 0:
            print(f"  [OK] Successfully pulled {image}")
            return True
        else:
            wait = initial_wait * attempt
            print(f"  [FAIL] Pull failed. Retrying in {wait}s...")
            time.sleep(wait)
    print(f"  [ERROR] Could not pull {image} after {max_retries} attempts.")
    return False

if __name__ == "__main__":
    failed = []
    for image in IMAGES:
        success = pull_with_retry(image)
        if not success:
            failed.append(image)

    if failed:
        print(f"\n[ERROR] Failed to pull: {failed}")
        print("Please check your internet connection and try again.")
        sys.exit(1)
    else:
        print("\n[OK] All images pulled. Now run: docker compose up --build -d")
