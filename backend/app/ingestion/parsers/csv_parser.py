import pandas as pd
from rapidfuzz import process, fuzz
import dateutil.parser
import warnings

# Suppress pandas warnings about empty columns
warnings.filterwarnings('ignore', category=FutureWarning)

CANONICAL_COLUMNS = {
    "cdr": {
        "caller_number": ["caller", "caller_number", "from_number", "a_party", "source_number"],
        "callee_number": ["callee", "to_number", "b_party", "destination_number", "callee_number"],
        "call_timestamp": ["timestamp", "call_time", "date_time", "time", "date"],
        "location": ["tower_location", "cell_id", "location", "tower", "site"]
    },
    "financial": {
        "sender_account": ["sender_account", "from_acc", "debit_acc", "source_account"],
        "receiver_account": ["receiver_account", "to_acc", "credit_acc", "destination_account"],
        "amount": ["amount", "txn_amount", "value", "transfer_amount"]
    }
}

def fuzzy_match_columns(df_columns):
    """Maps actual dataframe columns to canonical columns based on fuzzy matching."""
    mapped_columns = {}
    matched_canonical = set()
    
    for col in df_columns:
        best_match = None
        best_score = 0
        best_type = None
        
        for dtype, schema in CANONICAL_COLUMNS.items():
            for canonical_name, aliases in schema.items():
                if canonical_name in matched_canonical:
                    continue
                    
                match = process.extractOne(str(col).lower(), aliases, scorer=fuzz.token_sort_ratio)
                if match and match[1] > 80:  # 80% similarity threshold
                    if match[1] > best_score:
                        best_score = match[1]
                        best_match = canonical_name
                        best_type = dtype
                        
        if best_match:
            mapped_columns[col] = best_match
            matched_canonical.add(best_match)
            
    return mapped_columns

def detect_subtype(mapped_columns):
    """Determines if the file is CDR or Financial based on column counts."""
    cdr_count = sum(1 for v in mapped_columns.values() if v in CANONICAL_COLUMNS["cdr"])
    fin_count = sum(1 for v in mapped_columns.values() if v in CANONICAL_COLUMNS["financial"])
    
    if cdr_count > fin_count and cdr_count >= 2:
        return "cdr"
    elif fin_count > cdr_count and fin_count >= 2:
        return "financial"
    return "unknown"

def clean_dataframe(df, mapped_columns):
    """Normalizes data, strips whitespace, parses dates, collects warnings."""
    warnings_list = []
    
    # Rename columns to canonical names
    df = df.rename(columns=mapped_columns)
    
    # Drop completely empty rows
    initial_len = len(df)
    df = df.dropna(how='all')
    if len(df) < initial_len:
        warnings_list.append(f"Dropped {initial_len - len(df)} completely empty rows.")
    
    # Strip whitespace from strings
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].apply(lambda x: str(x).strip() if pd.notnull(x) else x)
            
    # Normalize dates if timestamp exists
    if "call_timestamp" in df.columns:
        def parse_date(d):
            if pd.isna(d): return d
            try: return dateutil.parser.parse(str(d)).isoformat()
            except: return d
        df["call_timestamp"] = df["call_timestamp"].apply(parse_date)
        
    # Check for malformed rows (missing essential canonical columns)
    essential_cols = []
    subtype = detect_subtype(mapped_columns)
    if subtype == "cdr":
        essential_cols = ["caller_number", "callee_number"]
    elif subtype == "financial":
        essential_cols = ["sender_account", "receiver_account", "amount"]
        
    if essential_cols:
        existing_essentials = [c for c in essential_cols if c in df.columns]
        if existing_essentials:
            before = len(df)
            df = df.dropna(subset=existing_essentials, how='any')
            if len(df) < before:
                warnings_list.append(f"Skipped {before - len(df)} rows due to missing essential data ({', '.join(existing_essentials)}).")

    return df, warnings_list

def parse_csv(file_path: str) -> dict:
    """Extracts structured data from a CSV or Excel file."""
    try:
        if file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
            
        mapped_columns = fuzzy_match_columns(df.columns)
        subtype = detect_subtype(mapped_columns)
        
        cleaned_df, warnings_list = clean_dataframe(df, mapped_columns)
        
        return {
            "data_shape": "structured",
            "content": cleaned_df,
            "detected_subtype": subtype,
            "warnings": warnings_list
        }
    except Exception as e:
        raise Exception(f"Failed to parse CSV/Excel: {str(e)}")
