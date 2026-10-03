# Demo Scenario: "Operation Crescent" (CASE-102)

This document provides the operational narrative for testing VERITAS during hackathon evaluations.

## Background Narrative

**Case Identifier**: `CASE-102`  
**Target Organization**: "Crescent Syndicate"  
**Primary Suspects**: Faisal Khan (alias "Faizal Cahn"), Vikram Sharma, Ahmed Raza  
**Involved Locations**: Hyderabad, Mumbai (Andheri), New Delhi  

"Operation Crescent" involves a organized financial fraud and illicit smuggling network operating across state borders. The network uses shell trading companies ("Crescent Traders"), multiple SIM cards registered under fake names, and structured bank transactions ("smurfing") to move illicit funds while evading detection by individual police stations.

## Evidence Materials Provided in Sample Files

Located in [`sample_evidence_files/`](file:///d:/SIH2026/sample_evidence_files):

1. **`FIR_001_Faisal_Khan.pdf`**: First Information Report filed at Andheri Police Station naming Faisal Khan, detailing a seizure of vehicle `MH-12-AB-1234` and phone number `+919876543210`.
2. **`CDR_Log_August2024.csv`**: Call Data Record listing 45 calls between `+919876543210`, `+919123456789` (Vikram Sharma), and secondary burner phones over a 72-hour period.
3. **`Bank_Transactions.json`**: Banking ledger recording 12 split transfers from `ACC-AHMED-4521` to accounts linked to "Crescent Traders" in amounts under INR 50,000 to avoid automatic reporting thresholds.

## Key Discovery Highlights During Demo

- **Cross-Source Fusion**: Connecting `FIR_001` with `CDR_Log` reveals that Faisal Khan called Vikram Sharma 14 minutes prior to the vehicle seizure.
- **Entity Resolution**: VERITAS automatically catches phonetic variant "Faizal Cahn" mentioned in an interrogation report, proposing a merge to the investigator.
- **Risk Scoring**: Faisal Khan is automatically flagged in **Red** due to high network degree ($\ge 5$) and cross-document presence.
