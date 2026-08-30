import re
from rapidfuzz import fuzz

def normalize_text(text: str) -> str:
    """Normalizes text by lowercasing and removing punctuation."""
    if not text:
        return ""
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', '', text)
    return " ".join(text.split())

def calculate_name_score(name1: str, name2: str) -> float:
    """Calculates name similarity using Jaro-Winkler."""
    if not name1 or not name2:
        return 0.0
    n1 = normalize_text(name1)
    n2 = normalize_text(name2)
    # Jaro-Winkler is excellent for names (emphasizes prefix matches)
    return fuzz.jaro_winkler_similarity(n1, n2) / 100.0

def calculate_phone_score(phone1: str, phone2: str) -> float:
    """Calculates phone similarity (Exact or partial suffix match)."""
    if not phone1 or not phone2:
        return 0.0
    p1 = re.sub(r'\D', '', str(phone1))
    p2 = re.sub(r'\D', '', str(phone2))
    
    if not p1 or not p2:
        return 0.0
    if p1 == p2:
        return 1.0
    # Match last 10 digits
    if p1[-10:] == p2[-10:] and len(p1[-10:]) == 10 and len(p2[-10:]) == 10:
        return 1.0
    return 0.0

def calculate_address_score(addr1: str, addr2: str) -> float:
    """Calculates address similarity using Token Set Ratio."""
    if not addr1 or not addr2:
        return 0.0
    a1 = normalize_text(addr1)
    a2 = normalize_text(addr2)
    # Token set ratio handles word reordering and partial overlap (e.g., missing apt number)
    return fuzz.token_set_ratio(a1, a2) / 100.0

def score_pair(entity_a: dict, entity_b: dict) -> float:
    """
    Computes a confidence score between 0.0 and 1.0 that entity_a and entity_b 
    are the same real-world identity.
    """
    name_score = calculate_name_score(entity_a.get('name', ''), entity_b.get('name', ''))
    phone_score = calculate_phone_score(entity_a.get('phone', ''), entity_b.get('phone', ''))
    addr_score = calculate_address_score(entity_a.get('address', ''), entity_b.get('address', ''))
    
    confidence = 0.0
    
    # Core weighting heuristics
    if phone_score == 1.0:
        # Same phone number - extremely strong signal
        confidence = 0.7 + (name_score * 0.3)
    elif addr_score > 0.8:
        # Same/similar address - strong signal
        confidence = 0.4 + (name_score * 0.6)
    else:
        # Just name match - capped at 0.7 without corroborating identifiers
        confidence = name_score * 0.7
        
    # Contextual boost: Co-occurrence in the same document
    doc_id_a = entity_a.get('doc_id')
    doc_id_b = entity_b.get('doc_id')
    if doc_id_a and doc_id_b and doc_id_a == doc_id_b:
        confidence += 0.05
        
    return min(1.0, confidence)
