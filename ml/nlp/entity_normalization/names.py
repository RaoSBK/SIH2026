import re

HONORIFICS_REGEX = r"^(?:Mr\.|Mrs\.|Ms\.|Shri\b|Smt\.|Dr\.|Adv\.|Inspector\b|Constable\b|Officer\b|Advocate\b|Prof\.)\s+"

def normalize_name(name_str: str) -> str:
    """
    Normalizes person names by removing honorifics, OCR noise, and trailing punctuation.
    
    Example: "Mr. Ravi Kumar!" -> "Ravi Kumar"
    """
    if not name_str:
        return ""
        
    cleaned = name_str.strip()
    # Strip honorifics iteratively
    for _ in range(2):
        cleaned = re.sub(HONORIFICS_REGEX, "", cleaned, flags=re.IGNORECASE).strip()
        
    # Remove OCR noise & non-alphanumeric punctuation except space and hyphen
    cleaned = re.sub(r"[^\w\s\-]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    
    # Title case if all caps or lowercase
    if cleaned.isupper() or cleaned.islower():
        cleaned = cleaned.title()
        
    return cleaned
