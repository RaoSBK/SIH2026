import re

ABBREVIATIONS = {
    r"\bP\.?S\b\.?": "Police Station",
    r"\bRd\b\.?": "Road",
    r"\bSt\b\.?": "Street",
    r"\bApt\b\.?": "Apartment",
    r"\bNgr\b\.?": "Nagar",
    r"\bMarg\b\.?": "Marg",
    r"\bDist\b\.?": "District",
    r"\bSec\b\.?": "Sector"
}

def normalize_location(loc_str: str) -> str:
    """
    Standardizes location strings and expands common geographical abbreviations.
    
    Example: "Andheri P.S." -> "Andheri Police Station"
             "MG Rd. Section 4" -> "MG Road Section 4"
    """
    if not loc_str:
        return ""
        
    cleaned = loc_str.strip()
    
    for pattern, replacement in ABBREVIATIONS.items():
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
    # Remove trailing punctuation (dots, commas)
    cleaned = re.sub(r"[.,;!?]+$", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    
    if cleaned.isupper() or cleaned.islower():
        cleaned = cleaned.title()
        
    return cleaned
