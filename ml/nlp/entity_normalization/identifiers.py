import re

def normalize_identifier(id_str: str, id_type: str = "VEHICLE") -> str:
    """
    Standardizes identifier formats (vehicle registration plates, case IDs, bank accounts).
    
    Example: "mh-12 ab 1234" -> "MH12AB1234"
             "case 102"      -> "CASE-102"
    """
    if not id_str:
        return ""
        
    cleaned = id_str.strip()
    id_type_upper = str(id_type).upper()
    
    if id_type_upper in ("VEHICLE", "PLATE"):
        # Remove hyphens and spaces, uppercase
        return re.sub(r"[^A-Za-z0-9]", "", cleaned).upper()
        
    elif id_type_upper in ("CASE", "CASE_ID"):
        digits = re.sub(r"\D", "", cleaned)
        if digits:
            return f"CASE-{digits.zfill(3)}"
        return cleaned.upper()
        
    elif id_type_upper in ("ACCOUNT", "BANK_ACCOUNT"):
        return re.sub(r"[^A-Za-z0-9]", "", cleaned).upper()
        
    return cleaned.upper()
