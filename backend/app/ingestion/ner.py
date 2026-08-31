"""
CIAS Entity Extraction Module — ner.py

Consumes the standardized parser output contract from Task 2:
  { "data_shape": "structured" | "unstructured" | "mixed",
    "content": DataFrame | str, "detected_subtype": str, "warnings": list }

Returns:
  { "entities": [...], "relationships": [...] }

Confidence semantics:
  - 1.0  → Deterministic (CDR row, financial row — ground truth)
  - 0.5  → NLP-inferred (proximity, verb cue) — "suggested, needs investigator confirmation"
"""

import re
import hashlib
import uuid
import pandas as pd
from typing import Optional

# ─── Lazy-loaded spaCy model ───────────────────────────────────────────────────
_NLP = None

def _get_nlp():
    global _NLP
    if _NLP is None:
        try:
            import sys, os
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            import spacy
            _NLP = spacy.load("en_core_web_sm")
        except OSError:
            raise RuntimeError(
                "spaCy model 'en_core_web_sm' not found. "
                "Run: python -m spacy download en_core_web_sm"
            )
    return _NLP


# ─── Regex patterns ────────────────────────────────────────────────────────────
PHONE_RE    = re.compile(r'\b(?:\+91[\-\s]?)?[6-9]\d{9}\b')
VEHICLE_RE  = re.compile(r'\b[A-Z]{2}[\s\-]?\d{1,2}[\s\-]?[A-Z]{1,3}[\s\-]?\d{4}\b')
FIR_RE      = re.compile(r'\bFIR[\s\-]?(?:No\.?|Number)?\s*[\d/]+\b', re.IGNORECASE)
AADHAAR_RE  = re.compile(r'\b\d{4}[\s\-]\d{4}[\s\-]\d{4}\b')

RELATIONSHIP_VERBS = {
    "called", "met", "visited", "transferred", "sent", "paid",
    "received", "worked", "associated", "linked", "contacted"
}


# ─── Helpers ───────────────────────────────────────────────────────────────────
def _make_id(entity_type: str, value: str) -> str:
    """Deterministic entity ID: type:sha8-of-value."""
    h = hashlib.sha256(value.encode()).hexdigest()[:8]
    return f"{entity_type.lower()}:{h}"

def _normalize_phone(raw: str) -> str:
    """Strip non-digits, ensure +91 prefix for 10-digit Indian numbers."""
    digits = re.sub(r'\D', '', raw)
    if len(digits) == 10:
        digits = '91' + digits
    if not digits.startswith('91'):
        digits = '91' + digits[-10:]
    return '+' + digits

def _normalize_account(raw: str) -> str:
    """Strip whitespace, uppercase."""
    return re.sub(r'\s+', '', raw).upper()

def _hash_aadhaar(raw: str) -> tuple[str, str]:
    """Return (sha256_hex, masked_display) — raw digits never stored."""
    digits = re.sub(r'\D', '', raw)
    sha = hashlib.sha256(digits.encode()).hexdigest()
    masked = 'XXXX-XXXX-' + digits[-4:]
    return sha, masked

def _make_entity(etype: str, value: str, confidence: float = 1.0, **attrs) -> dict:
    return {
        "id":         _make_id(etype, value),
        "type":       etype,
        "value":      value,
        "confidence": confidence,
        "attributes": attrs
    }

def _make_rel(rtype: str, source: str, target: str, confidence: float,
              evidence: str, status: str = "confirmed", **attrs) -> dict:
    return {
        "id":         str(uuid.uuid4()),
        "type":       rtype,
        "source":     source,
        "target":     target,
        "confidence": confidence,
        "status":     status,
        "evidence":   evidence,
        "attributes": attrs
    }


# ─── 3a: STRUCTURED PATH ───────────────────────────────────────────────────────
def _extract_structured(df: pd.DataFrame, subtype: str) -> tuple[list, list]:
    """
    Vectorized extraction from normalized DataFrames.
    Confidence = 1.0 (deterministic from source record).
    """
    entities = {}
    relationships = []

    if subtype == "cdr":
        # Vectorized phone normalization
        for col in ("caller_number", "callee_number"):
            if col in df.columns:
                df[col] = df[col].dropna().astype(str).apply(
                    lambda x: _normalize_phone(x) if re.search(r'\d{10}', x) else x
                )

        # Unique phone entities
        for col in ("caller_number", "callee_number"):
            if col in df.columns:
                for val in df[col].dropna().unique():
                    e = _make_entity("PHONE", val, confidence=1.0)
                    entities[e["id"]] = e

        # Relationships — one per CDR row (vectorized via itertuples for speed)
        caller_col  = "caller_number"  if "caller_number"  in df.columns else None
        callee_col  = "callee_number"  if "callee_number"  in df.columns else None
        ts_col      = "call_timestamp" if "call_timestamp" in df.columns else None
        dur_col     = "duration"       if "duration"       in df.columns else None
        loc_col     = "location"       if "location"       in df.columns else None

        for row in df.itertuples(index=True, name="CDRRow"):
            caller = getattr(row, caller_col, None) if caller_col else None
            callee = getattr(row, callee_col, None) if callee_col else None
            if not caller or not callee or pd.isna(caller) or pd.isna(callee):
                continue
            evidence = f"CDR row {row.Index}: {caller} -> {callee}"
            rel = _make_rel(
                rtype      = "CALLED",
                source     = _make_id("PHONE", str(caller)),
                target     = _make_id("PHONE", str(callee)),
                confidence = 1.0,
                evidence   = evidence,
                status     = "confirmed",
                timestamp  = str(getattr(row, ts_col, "")) if ts_col else "",
                duration   = str(getattr(row, dur_col, "")) if dur_col else "",
                location   = str(getattr(row, loc_col, "")) if loc_col else ""
            )
            relationships.append(rel)

    elif subtype == "financial":
        # Vectorized account normalization
        for col in ("sender_account", "receiver_account"):
            if col in df.columns:
                df[col] = df[col].dropna().astype(str).str.strip().str.upper()

        # Unique account entities
        for col in ("sender_account", "receiver_account"):
            if col in df.columns:
                for val in df[col].dropna().unique():
                    e = _make_entity("ACCOUNT", val, confidence=1.0)
                    entities[e["id"]] = e

        sender_col   = "sender_account"   if "sender_account"   in df.columns else None
        receiver_col = "receiver_account" if "receiver_account" in df.columns else None
        amount_col   = "amount"           if "amount"           in df.columns else None
        ts_col       = "call_timestamp"   if "call_timestamp"   in df.columns else None

        for row in df.itertuples(index=True, name="FinRow"):
            sender   = getattr(row, sender_col, None)   if sender_col else None
            receiver = getattr(row, receiver_col, None) if receiver_col else None
            if not sender or not receiver or pd.isna(sender) or pd.isna(receiver):
                continue
            evidence = f"Financial row {row.Index}: {sender} → {receiver}"
            rel = _make_rel(
                rtype      = "TRANSFERRED_TO",
                source     = _make_id("ACCOUNT", str(sender)),
                target     = _make_id("ACCOUNT", str(receiver)),
                confidence = 1.0,
                evidence   = evidence,
                status     = "confirmed",
                amount     = str(getattr(row, amount_col, "")) if amount_col else "",
                timestamp  = str(getattr(row, ts_col, ""))     if ts_col     else ""
            )
            relationships.append(rel)

    return list(entities.values()), relationships


# ─── 3b: UNSTRUCTURED PATH ─────────────────────────────────────────────────────
def _extract_unstructured(text: str, source_label: str = "") -> tuple[list, list]:
    """
    NLP + Regex extraction from free text.
    spaCy called ONCE for the whole document.
    NLP-inferred relationships: confidence=0.5, status='suggested'.
    """
    nlp = _get_nlp()
    entities = {}
    relationships = []

    # ── 1. Regex extractions ─────────────────────────────────────────────────
    for m in PHONE_RE.finditer(text):
        norm = _normalize_phone(m.group())
        e = _make_entity("PHONE", norm, confidence=0.9)
        entities[e["id"]] = e

    for m in VEHICLE_RE.finditer(text):
        veh = re.sub(r'[\s\-]', '', m.group()).upper()
        e = _make_entity("VEHICLE", veh, confidence=0.9)
        entities[e["id"]] = e

    for m in FIR_RE.finditer(text):
        fir = m.group().strip()
        e = _make_entity("FIR", fir, confidence=0.9)
        entities[e["id"]] = e

    # Aadhaar — SHA-256 hash, never raw
    for m in AADHAAR_RE.finditer(text):
        sha, masked = _hash_aadhaar(m.group())
        e = _make_entity("AADHAAR", masked, confidence=0.9,
                         id_hash=sha, display=masked)
        # Override id to use hash so we can dedup across documents
        e["id"] = f"aadhaar:{sha}"
        entities[e["id"]] = e

    # ── 2. spaCy — ONE call for the whole document ───────────────────────────
    doc = nlp(text)

    spacy_entities = {}  # span_text → entity dict
    for ent in doc.ents:
        val = ent.text.strip()
        if not val:
            continue
        if ent.label_ == "PERSON":
            e = _make_entity("PERSON", val, confidence=0.85)
        elif ent.label_ in ("GPE", "LOC"):
            e = _make_entity("LOCATION", val, confidence=0.85)
        elif ent.label_ == "ORG":
            e = _make_entity("ORG", val, confidence=0.85)
        else:
            continue
        entities[e["id"]] = e
        spacy_entities[val.lower()] = e

    # ── 3. Sentence-level proximity linking & relationship cues ──────────────
    for sent in doc.sents:
        sent_text = sent.text.strip()
        sent_entities = {}

        # Collect spaCy entities in this sentence
        for ent in sent.ents:
            val = ent.text.strip()
            if val.lower() in spacy_entities:
                sent_entities[val] = spacy_entities[val.lower()]

        # Collect regex entities in this sentence
        for m in PHONE_RE.finditer(sent_text):
            norm = _normalize_phone(m.group())
            eid = _make_id("PHONE", norm)
            if eid in entities:
                sent_entities[norm] = entities[eid]

        for m in VEHICLE_RE.finditer(sent_text):
            veh = re.sub(r'[\s\-]', '', m.group()).upper()
            eid = _make_id("VEHICLE", veh)
            if eid in entities:
                sent_entities[veh] = entities[eid]

        # Proximity linking: PERSON ↔ PHONE / PERSON ↔ VEHICLE in same sentence
        persons  = [e for e in sent_entities.values() if e["type"] == "PERSON"]
        phones   = [e for e in sent_entities.values() if e["type"] == "PHONE"]
        vehicles = [e for e in sent_entities.values() if e["type"] == "VEHICLE"]

        for person in persons:
            for phone in phones:
                rel = _make_rel(
                    rtype      = "HAS_PHONE",
                    source     = person["id"],
                    target     = phone["id"],
                    confidence = 0.5,
                    evidence   = sent_text,
                    status     = "suggested — needs investigator confirmation"
                )
                relationships.append(rel)
            for vehicle in vehicles:
                rel = _make_rel(
                    rtype      = "OWNS_VEHICLE",
                    source     = person["id"],
                    target     = vehicle["id"],
                    confidence = 0.5,
                    evidence   = sent_text,
                    status     = "suggested — needs investigator confirmation"
                )
                relationships.append(rel)

        # Relationship cue detection (verb triggers between any two entities)
        ent_list = list(sent_entities.values())
        sent_lower = sent_text.lower()
        triggered_verb = next(
            (v for v in RELATIONSHIP_VERBS if v in sent_lower), None
        )
        if triggered_verb and len(ent_list) >= 2:
            for i in range(len(ent_list)):
                for j in range(i + 1, len(ent_list)):
                    rel = _make_rel(
                        rtype      = triggered_verb.upper(),
                        source     = ent_list[i]["id"],
                        target     = ent_list[j]["id"],
                        confidence = 0.5,
                        evidence   = sent_text,
                        status     = "suggested — needs investigator confirmation",
                        trigger_verb = triggered_verb
                    )
                    relationships.append(rel)

    return list(entities.values()), relationships


# ─── Main Entry Point ──────────────────────────────────────────────────────────
def extract_entities(parsed_output: dict, source_label: str = "") -> dict:
    """
    Branches on data_shape from the Task 2 parser contract.

    Args:
        parsed_output: dict from parse_*(file_path)
        source_label: provenance label (e.g., "seed_loader", "investigator_upload")

    Returns:
        {"entities": [...], "relationships": [...]}
    """
    data_shape = parsed_output.get("data_shape", "unstructured")
    content    = parsed_output.get("content")
    subtype    = parsed_output.get("detected_subtype", "unknown")

    if data_shape == "structured" and isinstance(content, pd.DataFrame):
        entities, relationships = _extract_structured(content, subtype)

    elif data_shape in ("unstructured", "mixed"):
        # mixed = PDF with embedded tables already flattened to text by parser
        entities, relationships = _extract_unstructured(str(content), source_label)

    else:
        entities, relationships = [], []

    return {
        "entities":      entities,
        "relationships": relationships
    }
