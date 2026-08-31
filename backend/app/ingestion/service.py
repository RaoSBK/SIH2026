import os
from app.ingestion.parsers.pdf_parser import parse_pdf
from app.ingestion.parsers.docx_parser import parse_docx
from app.ingestion.parsers.csv_parser import parse_csv
from app.ingestion.parsers.json_parser import parse_json
from app.ingestion.parsers.txt_parser import parse_txt
from app.ingestion.ner import extract_entities
from app.ingestion.resolver import resolve_entities
from app.audit.logger import log_ingestion

def process_file(file_path: str, file_type: str = None, source_label: str = "unknown", case_id: str = None) -> dict:
    """
    Universal ingestion entry point enforcing strict data shape contract.
    Parses the file with the appropriate parser (Task 2), then extracts entities
    and relationships using ner.py (Task 3).
    """
    file_name = os.path.basename(file_path)

    if not file_type:
        _, ext = os.path.splitext(file_path)
        file_type = ext.lower().replace(".", "")

    try:
        # ── 1. Parsing Stage ─────────────────────────────────────────────────
        if file_type == "pdf":
            parsed = parse_pdf(file_path)
        elif file_type in ["docx", "doc"]:
            parsed = parse_docx(file_path)
        elif file_type in ["csv", "xlsx", "xls"]:
            parsed = parse_csv(file_path)
        elif file_type == "json":
            parsed = parse_json(file_path)
        elif file_type == "txt":
            parsed = parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: '{file_type}'")

        # ── 2. Entity & Relationship Extraction — ner.py (Task 3) ──────────
        extracted = extract_entities(parsed, source_label=source_label)

        # ── 3. Entity Resolution / Deduplication — resolver.py (Task 4) ────
        resolved = resolve_entities(extracted, source_file=file_name)
        entities      = resolved["resolved_entities"]
        relationships = resolved["resolved_relationships"]
        needs_review  = resolved["needs_review"]
        stats         = resolved["stats"]

        # ── 3. Build success summary ─────────────────────────────────────────
        result = {
            "status":                "success",
            "data_shape":            parsed["data_shape"],
            "detected_subtype":      parsed["detected_subtype"],
            "parser_warnings":       parsed["warnings"],
            "entities_found":        len(entities),
            "relationships_created": len(relationships),
            "needs_review":          needs_review,
            "resolution_stats":      stats,
            "data": {
                "nodes": entities,
                "links": relationships
            }
        }

        # ── 4. Audit log ─────────────────────────────────────────────────────
        log_ingestion(
            file_name=file_name,
            source_label=source_label,
            case_id=case_id,
            status="success",
            message=f"Extracted {len(entities)} entities, {len(relationships)} relationships. Shape: {parsed['data_shape']}.",
            entities_count=len(entities),
            new_nodes=len(entities)
        )
        return result

    except Exception as e:
        error_msg = str(e)
        log_ingestion(
            file_name=file_name,
            source_label=source_label,
            case_id=case_id,
            status="error",
            message=error_msg
        )
        return {
            "status":  "error",
            "stage":   "processing",
            "message": error_msg
        }
