# Security & Governance Architecture

This document outlines the security architecture protecting criminal intelligence data, evidence integrity, and user access within VERITAS.

Source Code: [`backend/app/auth/`](file:///d:/SIH2026/backend/app/auth/), [`blockchain/client/fabric_client.py`](file:///d:/SIH2026/blockchain/client/fabric_client.py)

## Core Security Pillars

### 1. Identity & Role-Based Access Control (RBAC)
User access is strictly enforced via OAuth2 Bearer JWT tokens (`backend/app/auth/jwt.py`):
- **`investigator`**: Can create cases, upload evidence, run pipelines, and resolve entity disambiguation queues.
- **`supervisor`**: Can assign cases to investigators, approve case closures, and inspect audit trails across all team cases.
- **`system_admin`**: Full administrative access to system configurations, user provisioning, and database maintenance.

### 2. Attribute-Based Case Isolation (ABAC)
Case data isolation is governed by `require_case_access` in `backend/app/auth/abac.py`. Investigators can only query or view graph data for cases specifically assigned to their user ID in PostgreSQL (`backend/app/cases/repository.py`).

### 3. Cryptographic Evidence Tamper-Proofing
All evidence file uploads calculate a SHA-256 digest prior to ingestion. Checksums are registered into a case-scoped Merkle Tree (`blockchain/client/fabric_client.py`), creating an immutable ledger (`evidence_ledger.json`). Any file modification invalidates the Merkle Root Hash.

### 4. PII Protection & Aadhaar Masking
Sensitive citizen identity numbers (such as Aadhaar) extracted during NER parsing are masked before UI presentation (`XXXX-XXXX-1234`). Raw Aadhaar digits are stored exclusively as SHA-256 hashes for identity matching purposes.
