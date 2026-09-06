"""
Document Relevance Validation Module — relevance.py

Evaluates parsed document text for domain relevance before running NER entity
extraction and graph insertion. Prevents non-investigative text (e.g. food menus,
receipts, general notes) from polluting the knowledge graph.
"""

import re
from typing import Union
from .ner import (
    PHONE_RE, AADHAAR_RE, VEHICLE_RE, FIR_RE, ACCOUNT_RE,
    NON_NAME_WORDS
)

# ─── Configurable Named Thresholds ─────────────────────────────────────────────
MIN_REGEX_MATCHES = 1
MIN_DOMAIN_KEYWORDS = 2

# ─── Domain Vocabulary (Extended from ner.py NON_NAME_WORDS) ────────────────────
INVESTIGATIVE_KEYWORDS = frozenset(NON_NAME_WORDS | {
    "fir", "case", "police", "station", "complainant", "accused", "victim", "witness",
    "informant", "suspect", "subject", "interrogation", "surveillance", "intel",
    "intelligence", "cdr", "call", "transaction", "bank", "account", "investigation",
    "crime", "criminal", "offence", "offense", "ipc", "crpc", "evidence", "seizure",
    "panchnama", "mumbai", "delhi", "phone", "mobile", "aadhaar", "vehicle", "passport",
    "nodal", "officer", "inspector", "constable", "si", "asi", "dfir", "cyber"
})


def assess_relevance(text: str) -> dict:
    """
    Evaluates whether a document text contains sufficient investigative signals
    (regex patterns or domain keywords) to warrant entity extraction and graph building.

    Returns:
        {
            "is_relevant": bool,
            "is_borderline": bool,
            "signal_count": int,
            "matched_regexes": list[str],
            "matched_keywords": list[str],
            "reason": str
        }
    """
    if not text or not isinstance(text, str):
        return {
            "is_relevant": False,
            "is_borderline": False,
            "signal_count": 0,
            "matched_regexes": [],
            "matched_keywords": [],
            "reason": "Empty or non-text document content."
        }

    # 1. Match deterministic regex patterns
    matched_regexes = []
    for label, pattern in [
        ("PHONE", PHONE_RE),
        ("AADHAAR", AADHAAR_RE),
        ("VEHICLE", VEHICLE_RE),
        ("FIR", FIR_RE),
        ("ACCOUNT", ACCOUNT_RE)
    ]:
        matches = pattern.findall(text)
        if matches:
            matched_regexes.extend([f"{label}:{m}" for m in matches[:3]])

    regex_count = len(matched_regexes)

    # 2. Match domain keywords
    words = set(re.findall(r'\b[a-z]{3,}\b', text.lower()))
    matched_keywords = sorted(list(words.intersection(INVESTIGATIVE_KEYWORDS)))
    keyword_count = len(matched_keywords)

    total_signal_count = regex_count + keyword_count
    is_relevant = (regex_count >= MIN_REGEX_MATCHES) or (keyword_count >= MIN_DOMAIN_KEYWORDS)

    # Borderline document definition:
    # Passed keyword threshold (>= 2) but has 0 deterministic regex patterns,
    # OR total signal count is exactly at threshold.
    is_borderline = is_relevant and (regex_count == 0 or total_signal_count <= MIN_DOMAIN_KEYWORDS)

    if is_relevant:
        reason = (
            f"Document passed relevance gate with {regex_count} pattern match(es) "
            f"and {keyword_count} domain keyword(s) ({', '.join(matched_keywords[:5])})."
        )
    else:
        reason = (
            f"Low relevance: found {regex_count} pattern matches (min {MIN_REGEX_MATCHES}) "
            f"and {keyword_count} domain keywords (min {MIN_DOMAIN_KEYWORDS}). "
            f"No investigative signal detected."
        )

    return {
        "is_relevant": is_relevant,
        "is_borderline": is_borderline,
        "signal_count": total_signal_count,
        "matched_regexes": matched_regexes,
        "matched_keywords": matched_keywords,
        "reason": reason
    }
