import pymupdf  # PyMuPDF
import pdfplumber

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

def parse_pdf(file_path: str) -> dict:
    """Extracts text and tables from a PDF file."""
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
            # In Phase 2:
            # for page in doc:
            #     pix = page.get_pixmap()
            #     img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            #     text += pytesseract.image_to_string(img) + "\n"
            
        # 3. Attempt Table Extraction
        table_text = extract_tables_with_plumber(file_path)
        if table_text.strip():
            text += "\n\n--- EXTRACTED TABLES ---\n" + table_text
            data_shape = "mixed"
            
        return {
            "data_shape": data_shape,
            "content": text,
            "detected_subtype": "unknown", # NLP layer classifies PDF subtype usually
            "warnings": warnings_list
        }
    except Exception as e:
        raise Exception(f"Failed to parse PDF: {str(e)}")
