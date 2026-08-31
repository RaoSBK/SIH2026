def parse_txt(file_path: str) -> dict:
    """Extracts raw text from a TXT file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
            
        return {
            "data_shape": "unstructured",
            "content": raw_text,
            "detected_subtype": "unknown",
            "warnings": []
        }
    except Exception as e:
        raise Exception(f"Failed to parse TXT: {str(e)}")
