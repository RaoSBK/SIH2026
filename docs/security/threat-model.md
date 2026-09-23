# Threat Model & Security Mitigations

This document outlines security threats considered in the design of VERITAS, active countermeasures currently implemented in code, and planned security enhancements.

---

## 1. Implemented Mitigations (Active in Code)

| Threat Vector | Attack Scenario | Active Countermeasure in Code | Implementation Source |
|---|---|---|---|
| **Evidence Tampering** | Adversary alters an uploaded FIR or CDR file post-ingestion to fabricate evidence or clear a suspect. | SHA-256 evidence file checksum calculated at upload; case Merkle Tree Root recomputed and logged to tamper-evident ledger (`evidence_ledger.json`). Verifiable via `/api/evidence/verify`. | [`blockchain/client/fabric_client.py`](file:///d:/SIH2026/blockchain/client/fabric_client.py) |
| **Unauthorized Case Access** | Investigator assigned to Case A attempts to query graph entities or CDR logs belonging to Case B. | Attribute-Based Case Isolation (`require_case_access`) checks PostgreSQL `case_assignments` before returning Cypher graph responses. | [`backend/app/auth/abac.py`](file:///d:/SIH2026/backend/app/auth/abac.py) |
| **Credential Hijacking / Session Replay** | Adversary intercepts user session to query network graphs. | Password hashing with `bcrypt` (cost factor 12); stateless OAuth2 JWT tokens with expiration claims (`exp`). | [`backend/app/auth/jwt.py`](file:///d:/SIH2026/backend/app/auth/jwt.py) |
| **Cypher / SQL Injection** | Malicious evidence text attempts Cypher query injection to leak graph database nodes. | Parameterized Cypher query parameters (`$case_id`, `$id`, `$attributes`) passed via Neo4j Bolt driver parameter maps instead of raw string concatenation. | [`backend/app/database/neo4j.py`](file:///d:/SIH2026/backend/app/database/neo4j.py) |

---

## 2. Planned Security Features (Roadmap / Extensions)

The following security features are scaffolded in project documentation or folder stubs, but are **not yet connected in active execution**:

- **Live Enterprise Hyperledger Fabric Peer Network**: Replacing the local `evidence_ledger.json` file with a multi-organization Hyperledger Fabric Raft consensus network (`blockchain/fabric/`).
- **Hardware Security Module (HSM) Signing**: Offloading SHA-256 evidence hashing and key signing to FIPS 140-2 Level 3 hardware security modules.
- **Automated Database Encryption-at-Rest**: Enforcing transparent database encryption (TDE) for PostgreSQL tables and Neo4j data directories.
