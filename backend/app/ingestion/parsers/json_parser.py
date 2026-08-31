import json
import pandas as pd

def parse_json(file_path: str) -> dict:
    """Extracts data from a JSON file, returning structured DataFrame or unstructured text."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Check if structured (List of Dicts)
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            df = pd.DataFrame(data)
            return {
                "data_shape": "structured",
                "content": df,
                "detected_subtype": "unknown",
                "warnings": ["JSON loaded as structured dataframe."]
            }
            
        # Otherwise, flatten into unstructured text
        text_values = []
        def extract_strings(obj):
            if isinstance(obj, dict):
                for v in obj.values():
                    extract_strings(v)
            elif isinstance(obj, list):
                for item in obj:
                    extract_strings(item)
            elif isinstance(obj, str):
                text_values.append(obj)
                
        extract_strings(data)
        return {
            "data_shape": "unstructured",
            "content": "\n".join(text_values),
            "detected_subtype": "unknown",
            "warnings": ["JSON loaded as flattened unstructured text."]
        }
        
    except Exception as e:
        raise Exception(f"Failed to parse JSON: {str(e)}")
