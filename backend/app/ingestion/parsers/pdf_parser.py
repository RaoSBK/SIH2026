import re
import pymupdf  # PyMuPDF
import pdfplumber
import pandas as pd

# ─── Bank statement detection heuristics ──────────────────────────────────────
# If the first 1000 chars of a PDF match these patterns, it's a bank statement
# and should be routed as structured data — never through spaCy NLP.
_BANK_HEADER_RE = re.compile(
    r'BANK\s+STATEMENT|ACCOUNT\s+STATEMENT|TRANSACTION\s+(HISTORY|DETAILS)',
    re.IGNORECASE
)
_TABLE_ROW_RE = re.compile(
    r'(Date|Timestamp)[\s|]+.*(Description|Narration|Particulars)[\s|]+.*(Amount|Debit|Credit)',
    re.IGNORECASE
)
_ACCOUNT_NUM_RE = re.compile(r'Account\s+Number[:\s]+([A-Za-z0-9\-]+)', re.IGNORECASE)
_ACCOUNT_NAME_RE = re.compile(r'Account\s+Name[:\s]+([A-Za-z0-9 &.\-]+)', re.IGNORECASE)


def extract_tables_with_plumber(file_path: str):
    """Attempts to extract tables from a PDF using pdfplumber."""
    table_texts = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        # Clean row and join with pipes for readability
                        cleaned_row = [str(cell).replace('\n', ' ').strip() if cell else "" for cell in row]
                        if any(cleaned_row):
                            table_texts.append(" | ".join(cleaned_row))
    except Exception as e:
        print(f"pdfplumber table extraction failed: {e}")
    return "\n".join(table_texts)


def _extract_bank_statement_as_structured(file_path: str) -> dict | None:
    """
    Fix D: Attempts to parse a bank statement PDF as a structured DataFrame,
    reusing the same 'financial' subtype contract as CSV financial files.
    Returns None if the table structure can't be reliably parsed.
    """
    try:
        # ── NEW: pull account header info from page 1 text ──
        with pymupdf.open(file_path) as doc:
            header_text = doc[0].get_text()[:800] if len(doc) > 0 else ""
        acc_num_match = _ACCOUNT_NUM_RE.search(header_text)
        acc_name_match = _ACCOUNT_NAME_RE.search(header_text)
        account_number = acc_num_match.group(1).strip() if acc_num_match else None
        account_name = acc_name_match.group(1).strip() if acc_name_match else None

        rows = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    # Use the first row as header
                    raw_header = [str(c).strip().lower().replace('\n', ' ') if c else "" for c in table[0]]

                    # Map columns: try to identify date, description, amount columns
                    date_col = next((i for i, h in enumerate(raw_header) if 'date' in h or 'timestamp' in h), None)
                    desc_col = next((i for i, h in enumerate(raw_header) if any(k in h for k in ('description', 'narration', 'particular'))), None)
                    debit_col = next((i for i, h in enumerate(raw_header) if 'debit' in h or 'withdrawal' in h), None)
                    credit_col = next((i for i, h in enumerate(raw_header) if 'credit' in h or 'deposit' in h), None)
                    amount_col = next((i for i, h in enumerate(raw_header) if h == 'amount'), None)

                    # Need at least a description column to be useful
                    if desc_col is None:
                        continue

                    for row in table[1:]:
                        if not row or not any(row):
                            continue
                        cells = [str(c).strip().replace('\n', ' ') if c else "" for c in row]

                        # Extract sender/receiver from description using regex
                        desc = cells[desc_col] if desc_col < len(cells) else ""
                        # Looks for "Transfer to Name" or "Payment from Name"
                        # Do NOT use re.IGNORECASE for the name part, otherwise [A-Z] won't enforce uppercase
                        name_match = re.search(
                            r'(?i:transfer|payment|sent|received|to|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})',
                            desc
                        )

                        # Determine amount — prefer debit/credit split, fall back to amount
                        amount = ""
                        if debit_col and debit_col < len(cells) and cells[debit_col]:
                            amount = f"-{cells[debit_col]}"
                        elif credit_col and credit_col < len(cells) and cells[credit_col]:
                            amount = cells[credit_col]
                        elif amount_col and amount_col < len(cells):
                            amount = cells[amount_col]

                        row_data = {
                            "date": cells[date_col] if date_col is not None and date_col < len(cells) else "",
                            "description": desc,
                            "amount": amount,
                            "person_mentioned": name_match.group(1) if name_match else "",
                        }
                        rows.append(row_data)

        if not rows:
            return None

        df = pd.DataFrame(rows)
        return {
            "data_shape": "structured",
            "content": df,
            "detected_subtype": "bank_statement",
            "warnings": [f"Bank statement parsed as structured table: {len(rows)} transactions extracted."],
            "statement_account_number": account_number,
            "statement_account_name": account_name,
        }
    except Exception as e:
        print(f"Bank statement structured parsing failed, falling back to text: {e}")
        return None


def parse_pdf(file_path: str) -> dict:
    """Extracts text and tables from a PDF file.

    Fix D: Bank statement PDFs are detected by header heuristics and parsed
    as structured data (DataFrames), bypassing spaCy NLP entirely. This prevents
    table cells like 'Timest@mp' and 'Transfer to Ravi Kumar' from being fed to
    the NER engine and producing garbage person entities.
    """
    text = ""
    warnings_list = []
    data_shape = "unstructured"

    try:
        # 1. Attempt standard text extraction
        with pymupdf.open(file_path) as doc:
            for page in doc:
                text += page.get_text() + "\n"

        # 2. Check for Scanned / Image-heavy PDF
        if len(text.strip()) < 50:
            warnings_list.append("PDF appears to be a scanned image. OCR fallback is mocked for Phase 1.")
            text += "\n[MOCKED OCR TEXT WOULD APPEAR HERE]"

        # Fix D: Detect bank statements by heuristic and route as structured
        preview = text[:1500]
        if _BANK_HEADER_RE.search(preview) or _TABLE_ROW_RE.search(preview):
            structured = _extract_bank_statement_as_structured(file_path)
            if structured:
                return structured
            # If structured parse failed, fall through to text path with a warning
            warnings_list.append(
                "Detected bank statement but structured parse failed — "
                "falling back to text NLP. Expect lower accuracy."
            )

        # 3. Attempt Table Extraction (for non-bank-statement tables in mixed docs)
        table_text = extract_tables_with_plumber(file_path)
        if table_text.strip():
            text += "\n\n--- EXTRACTED TABLES ---\n" + table_text
            data_shape = "mixed"

        return {
            "data_shape": data_shape,
            "content": text,
            "detected_subtype": "unknown",
            "warnings": warnings_list
        }
    except Exception as e:
        raise Exception(f"Failed to parse PDF: {str(e)}")
