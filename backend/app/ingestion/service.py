import os
import asyncio
from .parsers.pdf_parser import parse_pdf
from .parsers.docx_parser import parse_docx
from .parsers.csv_parser import parse_csv
from .parsers.json_parser import parse_json
from .parsers.txt_parser import parse_txt
from .relevance import assess_relevance
from .ner import extract_entities
from .resolver import resolve_entities
from ..audit.logger import log_ingestion
from ..database.neo4j import insert_graph_data

def process_file(file_path: str, file_type: str = None, source_label: str = "unknown", case_id: str = None) -> dict:
    """
    Universal ingestion entry point enforcing strict data shape contract.
    Parses the file with the appropriate parser (Task 2), evaluates document relevance,
    and then extracts entities and relationships using ner.py (Task 3).
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

        # ── 1.5 Document Relevance Gate ──────────────────────────────────────
        content_text = ""
        if isinstance(parsed.get("content"), str):
            content_text = parsed["content"]
        elif hasattr(parsed.get("content"), "to_string"):
            content_text = parsed["content"].to_string()

        rel_info = assess_relevance(content_text)
        if not rel_info["is_relevant"]:
            message = f"Skipped — document rejected by relevance gate: {rel_info['reason']}"
            log_ingestion(
                file_name=file_name,
                source_label=source_label,
                case_id=case_id,
                status="rejected_low_relevance",
                message=message,
                entities_count=0,
                new_nodes=0
            )
            return {
                "status": "rejected_low_relevance",
                "reason": rel_info["reason"],
                "message": message,
                "data_shape": parsed.get("data_shape", "unstructured"),
                "detected_subtype": parsed.get("detected_subtype", "unknown"),
                "parser_warnings": parsed.get("warnings", []),
                "entities_found": 0,
                "relationships_created": 0,
                "needs_review": [],
                "resolution_stats": {"new": 0, "merged": 0, "flagged": 0},
                "data": {"nodes": [], "links": []}
            }

        # ── 2. Entity & Relationship Extraction — ner.py (Task 3) ──────────
        extracted = extract_entities(parsed, source_label=source_label)

        # ── 3. Entity Resolution / Deduplication — resolver.py (Task 4) ────
        resolved = resolve_entities(
            extracted,
            source_file=file_name,
            case_id=case_id,
        )
        entities      = resolved["resolved_entities"]
        relationships = resolved["resolved_relationships"]
        needs_review  = resolved["needs_review"]
        stats         = resolved["stats"]

        # Borderline document handling: force uncorroborated NLP entities into review
        if rel_info["is_borderline"]:
            for entity in entities:
                if entity.get("confidence", 1.0) <= 0.5 and entity.get("type") in ("PERSON", "LOCATION", "ORG"):
                    entity["status"] = "REVIEW_REQUIRED"
                    entity["flagged"] = True
                    needs_review.append({
                        "action": "borderline_document_entity",
                        "type": entity["type"],
                        "incoming": entity["value"],
                        "entity_id": entity["id"],
                        "confidence": entity.get("confidence", 0.5),
                        "reason": f"NLP-inferred {entity['type']} in borderline document (0 regex signals)",
                        "merge_action": "pending"
                    })

        # ── 4. Graph Database Insertion (Task 5) ─────────────────────────
        try:
            # Clear stale data from any previous ingestion of this same file
            from ..database.neo4j import delete_entities_by_source
            delete_entities_by_source(file_name=file_name, case_id=case_id)
        except Exception as e:
            print(f"Warning: could not clear prior ingestion data for {file_name}: {e}")

        try:
            insert_graph_data(entities, relationships, file_name=file_name, case_id=case_id)
        except Exception as e:
            print(f"Neo4j insertion failed: {e}")
            parsed["warnings"].append(f"Failed to persist graph data to Neo4j: {str(e)}")

        # ── 5. Build success summary ─────────────────────────────────────────
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

        # ── 6. Audit log ─────────────────────────────────────────────────────
        log_ingestion(
            file_name=file_name,
            source_label=source_label,
            case_id=case_id,
            status="success",
            message=f"Extracted {len(entities)} entities, {len(relationships)} relationships. Shape: {parsed['data_shape']}.",
            entities_count=len(entities),
            new_nodes=stats.get("new", 0),
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

