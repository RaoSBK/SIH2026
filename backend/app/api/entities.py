import os
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Entities & Disambiguation"])

class ReviewAction(BaseModel):
    action: str  # 'merge', 'reject', 'skip'

REGISTRY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/entity_registry.json"))

@router.get("/needs-review")
def get_needs_review():
    """Returns all ambiguous entity matches pending investigator confirmation."""
    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"entities": {}}

@router.get("/review-queue")
def get_review_queue():
    """
    Aggregates all pending REVIEW_REQUIRED items from the entity registry.
    """
    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "pending_review": data.get("needs_review", []),
            "total": len(data.get("needs_review", [])),
        }
    except Exception:
        return {"pending_review": [], "total": 0}

@router.post("/review-queue/{review_id}/resolve")
def resolve_review_item(review_id: str, payload: ReviewAction):
    """
    Resolves a pending entity review item with action 'merge', 'reject', or 'skip'.
    """
    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        needs_review = data.get("needs_review", [])
        updated_queue = []
        resolved_item = None

        for item in needs_review:
            item_id = ""
            if item.get("type") == "PHONE_CONFLICT":
                item_id = "-".join(item.get("names", []))
            else:
                c = item.get("candidate", {}).get("id", "")
                p = item.get("possible_match", {}).get("id", "")
                item_id = f"{c}-{p}"

            if item_id == review_id:
                resolved_item = item
            else:
                updated_queue.append(item)

        data["needs_review"] = updated_queue

        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        if payload.action == "merge" and resolved_item and resolved_item.get("type") == "PERSON_NAME_AMBIGUITY":
            try:
                from ..database.neo4j import merge_nodes_in_neo4j
                source_id = resolved_item.get("candidate", {}).get("id")
                target_id = resolved_item.get("possible_match", {}).get("id")
                if source_id and target_id:
                    merge_nodes_in_neo4j(source_id, target_id)
            except Exception as ex:
                logger.warning(f"Neo4j merge notice: {ex}")

        logger.info(f"Resolved review item {review_id} with action: {payload.action}")
        return {"status": "success", "action": payload.action, "remaining": len(updated_queue)}

    except Exception as e:
        logger.error(f"Failed to resolve review item: {e}")
        return {"status": "error", "message": str(e)}
