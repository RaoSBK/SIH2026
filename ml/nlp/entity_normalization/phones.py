import re

def normalize_phone(phone_str: str) -> str:
    """
    Standardizes phone numbers into clean 10-digit strings.
    
    Example: "+91-98765 43210" -> "9876543210"
             "09876543210"     -> "9876543210"
    """
    if not phone_str:
        return ""
        
    # Remove all non-digit characters
    digits = re.sub(r"\D", "", phone_str)
    
    # Strip leading country code 91 or 091 or 0
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    elif len(digits) > 10:
        digits = digits[-10:]
        
    if len(digits) == 10:
        return digits
    return digits if digits else phone_str.strip()
