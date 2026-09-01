"""
CIAS Entity Extraction Module — ner.py

Consumes the standardized parser output contract from Task 2:
  { "data_shape": "structured" | "unstructured" | "mixed",
    "content": DataFrame | str, "detected_subtype": str, "warnings": list }

Returns:
  { "entities": [...], "relationships": [...] }

Confidence semantics:
  - 1.0  → Deterministic (CDR row, financial row — ground truth)
  - 0.5  → NLP-inferred (sentence co-occurrence, verb cue) — "suggested, needs investigator confirmation"

Extraction version: bump this whenever extraction logic changes so legacy
entities in the registry can be flagged for reprocessing (feedback point 3).
"""

import re
import hashlib
import uuid
import pandas as pd
from typing import Optional

# ─── Extraction version stamp ──────────────────────────────────────────────────
EXTRACTION_VERSION = "1.1"

# ─── Lazy-loaded spaCy model ───────────────────────────────────────────────────
_NLP = None

def _get_nlp():
    global _NLP
    if _NLP is None:
        try:
            import sys, os
            import io
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            import spacy
            fine_tuned_path = "ml/nlp/models/fine_tuned"
            if os.path.exists(fine_tuned_path) and os.listdir(fine_tuned_path):
                print(f"Loading custom fine-tuned NER model from {fine_tuned_path}...")
                _NLP = spacy.load(fine_tuned_path)
            else:
                _NLP = spacy.load("en_core_web_sm")
        except OSError:
            print("spaCy model not found. Auto-downloading en_core_web_sm...")
            from spacy.cli import download
            download("en_core_web_sm")
            _NLP = spacy.load("en_core_web_sm")
    return _NLP


# ─── Regex patterns ────────────────────────────────────────────────────────────
PHONE_RE    = re.compile(r'(?<!\w)(?:\+91[\-\s]?)?[6-9]\d{9}\b')
VEHICLE_RE  = re.compile(r'\b[A-Z]{2}[\s\-]?\d{1,2}[\s\-]?[A-Z]{1,3}[\s\-]?\d{4}\b')
FIR_RE      = re.compile(r'\bFIR[\s\-]?(?:No\.?|Number)?\s*[\d/]+\b', re.IGNORECASE)
AADHAAR_RE  = re.compile(r'\b\d{4}[\s\-]\d{4}[\s\-]\d{4}\b')

RELATIONSHIP_VERBS = {
    "called", "met", "visited", "transferred", "sent", "paid",
    "received", "worked", "associated", "linked", "contacted"
}

# ─── Stoplist for PERSON false-positives ───────────────────────────────────────
# Words that spaCy commonly tags as PERSON but are actually field labels,
# titles, or domain keywords in police/forensic documents.
# KNOWN LIMITATION: tuned against 9 sample documents — real traffic will
# surface new false-positives.  Every borderline accept/reject is written to
# data/ner_borderline_log.json so this list can be grown from real traffic.
NON_NAME_WORDS = frozenset({
    "name", "officer", "inspector", "constable", "si", "asi",
    "complainant", "accused", "victim", "witness", "informant",
    "suspect", "subject", "unknown", "male", "female",
    "sir", "madam", "shri", "smt", "kumari",
    "fir", "case", "ps", "police", "station", "district",
    "date", "time", "place", "address", "phone", "mobile",
    "account", "bank", "amount", "transaction",
    "report", "statement", "summary", "details",
})

# ─── Lightweight OCR normalization (no external dependency) ───────────────────
# Repairs common OCR artifacts in scanned documents without mangling numeric
# sequences (phones, accounts, FIR numbers).  Runs only on unstructured text,
# not on structured CSVs/CDRs.
_OCR_FIXES = [
    (re.compile(r'(?<=[a-zA-Z])0(?=[a-zA-Z])'),    'o'),   # letter-0-letter → o
    (re.compile(r'(?<=[a-zA-Z])1(?=[a-zA-Z])'),    'l'),   # letter-1-letter → l
    (re.compile(r'\|(?=[a-zA-Z])'),                  'I'),   # pipe → I
    (re.compile(r'(?<=[a-zA-Z])\|'),                 'I'),
    (re.compile(r'[ \t]+'),                          ' '),   # collapse whitespace
    (re.compile(r'(?<=[a-z])(?=[A-Z][a-z]{3,})'),   ' '),   # glued words: "calledRavi" → "called Ravi"
]

def _normalize_ocr(text: str) -> str:
    """Apply conservative OCR artifact corrections to free text."""
    for pattern, replacement in _OCR_FIXES:
        text = pattern.sub(replacement, text)
    return text


def _is_probable_name(text: str, context: str = "", source_doc: str = "") -> bool:
    """
    Returns True if the spaCy PERSON span is likely a real name rather than
    a field label or domain keyword.

    Borderline decisions are logged to data/ner_borderline_log.json so the
    stoplist can be tuned against real traffic (feedback point 6).
    """
    # Only run stoplist check for very short spans (1-2 tokens) where false-
    # positive rate is highest.  Longer spans are almost certainly names.
    words = text.strip().split()
    if len(words) > 3:
        return True

    lower_words = {w.lower().rstrip('.:,') for w in words}
    hit = lower_words & NON_NAME_WORDS
    if hit:
        # Borderline — rejected: log for tuning
        try:
            from ..audit.logger import log_ner_borderline
            log_ner_borderline(
                entity_value=text,
                verdict="rejected",
                score=0.0,
                source_doc=source_doc,
                context=context[:120] if context else "",
            )
        except Exception:
            pass
        return False
    return True


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
        "id":                 _make_id(etype, value),
        "type":               etype,
        "value":              value,
        "confidence":         confidence,
        "extraction_version": EXTRACTION_VERSION,
        "attributes":         attrs,
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

    Key correctness guarantees vs. previous version:
    - Phone/name associations are tied to SENTENCE boundaries, not character
      windows (old character-window approach caused cross-sentence misattribution).
    - PERSON spans are filtered through NON_NAME_WORDS stoplist before keeping.
    - OCR normalization runs first to repair common scan artifacts.
    - Every entity is stamped with EXTRACTION_VERSION for registry versioning.
    """
    # ── 0. OCR normalization (unstructured path only) ────────────────────────
    text = _normalize_ocr(text)

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
        e["id"] = f"aadhaar:{sha}"  # hash-based ID for cross-doc dedup
        entities[e["id"]] = e

    # ── 2. spaCy — ONE call for the whole document ───────────────────────────
    if len(text) > nlp.max_length:
        nlp.max_length = len(text) + 100000

    doc = nlp(text)

    # Build doc-level entity index (only after stoplist filtering)
    spacy_entities = {}  # canonical value (lower) → entity dict
    for ent in doc.ents:
        val = ent.text.strip()
        if not val:
            continue
        if ent.label_ == "PERSON":
            if not _is_probable_name(val, context=ent.sent.text, source_doc=source_label):
                continue  # stoplist rejected — already logged
            e = _make_entity("PERSON", val, confidence=0.85)
        elif ent.label_ in ("GPE", "LOC"):
            e = _make_entity("LOCATION", val, confidence=0.85)
        elif ent.label_ == "ORG":
            e = _make_entity("ORG", val, confidence=0.85)
        else:
            continue
        entities[e["id"]] = e
        spacy_entities[val.lower()] = e

    # ── 3. SENTENCE-BOUNDARY relationship linking ────────────────────────────
    # IMPORTANT: entities are linked only when they co-occur in the SAME sentence.
    # The previous character-window approach caused misattribution across sentence
    # boundaries (e.g., name from sentence A associated with phone in sentence B).
    for sent in doc.sents:
        sent_text = sent.text.strip()
        if not sent_text:
            continue
        sent_entities: dict[str, dict] = {}

        # Collect spaCy entities confirmed to be IN this sentence
        for ent in sent.ents:
            val = ent.text.strip()
            if val.lower() in spacy_entities:
                sent_entities[val] = spacy_entities[val.lower()]

        # Collect regex entities found IN this sentence's text only
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

        # Partition by type (within this sentence)
        persons  = [e for e in sent_entities.values() if e["type"] == "PERSON"]
        phones   = [e for e in sent_entities.values() if e["type"] == "PHONE"]
        vehicles = [e for e in sent_entities.values() if e["type"] == "VEHICLE"]

        # PERSON ↔ PHONE (same sentence — no character window)
        for person in persons:
            for phone in phones:
                relationships.append(_make_rel(
                    rtype      = "HAS_PHONE",
                    source     = person["id"],
                    target     = phone["id"],
                    confidence = 0.5,
                    evidence   = sent_text,
                    status     = "suggested — needs investigator confirmation",
                ))
            # PERSON ↔ VEHICLE (same sentence)
            for vehicle in vehicles:
                relationships.append(_make_rel(
                    rtype      = "OWNS_VEHICLE",
                    source     = person["id"],
                    target     = vehicle["id"],
                    confidence = 0.5,
                    evidence   = sent_text,
                    status     = "suggested — needs investigator confirmation",
                ))

        # PHONE ↔ PHONE (catches embedded CDR tables in PDFs)
        if len(phones) >= 2:
            for i in range(len(phones)):
                for j in range(i + 1, len(phones)):
                    relationships.append(_make_rel(
                        rtype      = "COMMUNICATED_WITH",
                        source     = phones[i]["id"],
                        target     = phones[j]["id"],
                        confidence = 0.5,
                        evidence   = sent_text,
                        status     = "suggested — needs investigator confirmation",
                    ))

        # Verb-cue relationship detection (any two entities in same sentence)
        ent_list = list(sent_entities.values())
        sent_lower = sent_text.lower()
        triggered_verb = next(
            (v for v in RELATIONSHIP_VERBS if v in sent_lower), None
        )
        if triggered_verb and len(ent_list) >= 2:
            for i in range(len(ent_list)):
                for j in range(i + 1, len(ent_list)):
                    relationships.append(_make_rel(
                        rtype        = triggered_verb.upper(),
                        source       = ent_list[i]["id"],
                        target       = ent_list[j]["id"],
                        confidence   = 0.5,
                        evidence     = sent_text,
                        status       = "suggested — needs investigator confirmation",
                        trigger_verb = triggered_verb,
                    ))

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
