# Evaluator Demo Script & Step-by-Step Walkthrough

This document provides a step-by-step evaluation walkthrough designed for Smart India Hackathon (SIH) 2026 judges to test the VERITAS application in 60-90 seconds.

## Demo Credentials & Access

- **Role**: Lead Investigator (`investigator`)
- **Default Account**: Username: `rao.a` | Password: `veritas`
- **Default Case ID**: `CASE-102` ("Operation Crescent")
- **Live Deployment**: `[INSERT_VERCEL_DEPLOYMENT_URL]` *(or local `http://localhost:3000`)*

---

## Step-by-Step Evaluator Walkthrough

```
 ┌───────────────────────────────┐
 │ 1. Authenticate & Select Case │
 └───────────────┬───────────────┘
                 ▼
 ┌───────────────────────────────┐
 │ 2. Ingest Evidence Documents  │ (Upload PDF/CSV/JSON)
 └───────────────┬───────────────┘
                 ▼
 ┌───────────────────────────────┐
 │ 3. Monitor Real-Time Pipeline │ (WebSocket Stages 0 -> 7)
 └───────────────┬───────────────┘
                 ▼
 ┌───────────────────────────────┐
 │ 4. Inspect Network Force Graph│ (D3.js Graph + Risk Color Highlighting)
 └───────────────┬───────────────┘
                 ▼
 ┌───────────────────────────────┐
 │ 5. Resolve Ambiguous Entities │ (/api/review-queue -> Merge/Reject)
 └───────────────┬───────────────┘
                 ▼
 ┌───────────────────────────────┐
 │ 6. Verify Evidence Integrity  │ (SHA-256 & Merkle Tree Root)
 └───────────────────────────────┘
```

### Step 1: Authenticate & Launch Console
1. Open the console interface in your browser.
2. Sign in with username `rao.a` and password `veritas` (or proceed directly to the open console dashboard).
3. Confirm active case selection is set to **`CASE-102`**.

### Step 2: Upload Evidence Documents
1. Navigate to the **Evidence Upload** panel.
2. Select sample evidence files from `sample_evidence_files/`:
   - `FIR_001_Faisal_Khan.pdf` (Narrative naming suspects & vehicles)
   - `CDR_Log_August2024.csv` (Call records between targets)
   - `Bank_Transactions.json` (Financial transfers)
3. Click **Process Evidence**.

### Step 3: Monitor Real-Time Pipeline Processing
1. Observe the live stage execution progress bar pushing real-time updates via WebSockets:
   - `Stage 0: Ingest` -> Calculating SHA-256 digests
   - `Stage 1: Normalize` -> Standardizing E.164 phone numbers
   - `Stage 2: Extract` -> Running multilingual spaCy NER
   - `Stage 3: Resolve` -> Running Jaro-Winkler & Double Metaphone entity resolution
   - `Stage 4: Graph` -> Writing nodes and edges to Neo4j
   - `Stage 5: Analyze` -> Running Isolation Forest & degree rule scoring
   - `Stage 6: Explain` -> Attaching risk colors & evidence trails

### Step 4: Explore Interactive Force-Directed Graph
1. Observe the interactive D3.js network canvas.
2. Note color-coded node indicators:
   - 🔴 **Red Nodes**: High-risk entities (e.g. `Faisal Khan`, connection degree $\ge 5$, multi-source implication).
   - 🟠 **Orange Nodes**: Medium-risk suspicious entities.
   - 🔵 **Blue/Grey Nodes**: Standard entities.
3. Click on **Faisal Khan** to expand the **Entity Inspection Drawer**:
   - Inspect the **Evidence Trail** verifying provenance across FIRs, CDRs, and bank transactions.
   - Click **Trace Shortest Path** to view direct communication links to co-conspirators.

### Step 5: Entity Disambiguation Review Queue
1. Click on the **Review Queue** tab.
2. Note the pending ambiguous identity match:
   - Candidate: `Faisal Khan` vs. `Faizal Cahn` (Double Metaphone Match `FS LK`, score 0.81).
3. Click **Merge**. Observe the live graph update consolidating both nodes into a single master entity with updated alias attributes.

### Step 6: Verify Cryptographic Evidence Tamper-Proofing
1. Click **Evidence Ledger / Audit Trail**.
2. View the registered SHA-256 file checksums and current **Case Merkle Root Hash**.
3. Click **Verify File Checksum** on `FIR_001_Faisal_Khan.pdf` to confirm status reads **`VERIFIED_TAMPER_EVIDENT`**.
