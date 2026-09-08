def parse_txt(file_path: str) -> dict:
    """Extracts raw text from a TXT file supporting multiple encodings."""
    raw_text = None
    encodings = ["utf-8", "utf-8-sig", "utf-16", "latin-1", "cp1252"]
    
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                raw_text = f.read()
                if raw_text:
                    break
        except Exception:
            continue
            
    if raw_text is None:
        raise Exception("Failed to decode TXT file with supported encodings (utf-8, utf-16, latin-1, cp1252).")
        
    return {
        "data_shape": "unstructured",
        "content": raw_text,
        "detected_subtype": "unknown",
        "warnings": []
    }
