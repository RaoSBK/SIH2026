# Data Privacy & Sensitive Information Protection

VERITAS handles sensitive criminal evidence files, personal data, and national identity numbers. This document outlines data privacy protection mechanisms implemented across the platform.

Source Code: [`backend/app/ingestion/ner.py`](file:///d:/SIH2026/backend/app/ingestion/ner.py#L408)

---

## 1. Aadhaar & PII Masking

- **Identification**: Aadhaar identity numbers (12-digit Indian national identity numbers) are parsed using Verhoeff algorithm regex validation during NER processing.
- **Masked Presentation**: Full Aadhaar numbers are never rendered in plain text across UI drawers, graph tooltips, or audit logs. They are masked to display only the last 4 digits (e.g. `XXXX-XXXX-1234`).
- **Cryptographic Hashing**: To preserve identity matching capabilities without storing plain text PII, Aadhaar numbers are stored using SHA-256 digests (`sha256_hash`).

---

## 2. Evidence File Isolation & Temporary File Storage

- Temporary files created during multi-part file uploads (`temp_uploads/`) are processed asynchronously in memory or isolated workspace directories.
- Upon pipeline job completion (`Stage 7`), temporary source files are securely deleted from temporary disk space (`os.remove()`).
- File storage paths are restricted to case-scoped directories.
