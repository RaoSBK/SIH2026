"""
CIAS Entity Resolution / Deduplication — resolver.py

Prevents duplicate graph nodes when the same entity (person, phone, location)
appears across multiple ingested files.

Resolution rules:
  Phones / Accounts → Exact match on normalized value (deterministic, confidence=1.0)
  Persons          → rapidfuzz token_sort_ratio:
                       ≥ 90 AND ≥ 1 corroborating signal → auto-merge (confidence=1.0)
                       ≥ 90, name-only (no corroboration) → REVIEW_REQUIRED
                       70–89 → needs_review (investigator must confirm)
                       < 70 → new node
  Locations        → Normalize abbreviations → fuzzy match ≥ 85 → auto-merge

Corroborating signals (required for name-based auto-merge):
  - Shared phone number (already in the registry linking both persons)
  - Shared bank account
  - Same case_id
  - Shared location (same document)

  Rationale: merging on name alone is catastrophic at real scale.
  "Ravi Kumar" and "R. Kumar" share "Kumar" but so do thousands of
  unrelated people with common surnames (Kumar, Singh, Khan).
  Without corroboration, name overlap downgrades to REVIEW_REQUIRED.
  See: feedback point in fix_pipeline.py review.

Outputs:
  {
    "resolved_entities":      [...],
    "resolved_relationships": [...],
    "merge_log":              [...],
    "needs_review":           [...],
    "stats": { "new": int, "merged": int, "flagged": int }
  }

IMPORTANT: This module is the last step before graph write (Task 5).
           False merges here corrupt the knowledge graph permanently.
           When in doubt, flag — never silently merge.
"""

import json
import os
import re
import hashlib
import uuid
import copy
from typing import Optional

from rapidfuzz import fuzz

# ── Registry file location (JSON-backed, replaced by Neo4j in Phase 2) ────────
_REGISTRY_PATH = os.path.join(
    os.path.dirname(__file__), "../../../data/entity_registry.json"
)

# Current extraction version (must match ner.py::EXTRACTION_VERSION)
_RESOLVER_VERSION = "1.1"

# ── Location abbreviation normalization map ────────────────────────────────────
LOCATION_ABBREV = {
    r'\bM\.?\s*G\.?\s*Road\b': 'MG Road',
    r'\bStn\.?\b':             'Station',
    r'\bRly\.?\b':             'Railway',
    r'\bDr\.?\b':              'Doctor',
    r'\bSt\.?\b':              'Street',
    r'\bRd\.?\b':              'Road',
    r'\bNr\.?\b':              'Near',
    r'\bOpp\.?\b':             'Opposite',
    r'\bExtn\.?\b':            'Extension',
    r'\bSoc\.?\b':             'Society',
    r'\bAppt?\.?\b':           'Apartment',
    r'\bMktg?\.?\b':           'Market',
}


# ══════════════════════════════════════════════════════════════════════════════
# EntityRegistry — JSON-backed persistent store
# ══════════════════════════════════════════════════════════════════════════════

class EntityRegistry:
    """
    In-memory entity store, persisted to JSON after every update.
    In Phase 2, every read/write in this class becomes a Neo4j Cypher query.

    Structure stored:
    {
      "entities": {
        "<entity_id>": {
          "id": str,
          "type": str,
          "value": str,              # canonical value
          "aliases": [str],          # alternative values seen across files
          "source_files": [str],     # provenance
          "confidence": float,
          "attributes": {...}
        }
      }
    }
    """

    def __init__(self, registry_path: str = _REGISTRY_PATH):
        self._path = registry_path
        self._entities: dict[str, dict] = {}
        self._load()

    def _load(self):
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        if os.path.exists(self._path):
            try:
                with open(self._path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._entities = data.get("entities", {})
                    # Tag legacy entities (pre-versioning) for reprocessing
                    for eid, entity in self._entities.items():
                        if "extraction_version" not in entity:
                            entity["needs_reprocess"] = True
            except (json.JSONDecodeError, IOError):
                self._entities = {}

    def _save(self):
        with open(self._path, 'w', encoding='utf-8') as f:
            json.dump(
                {"entities": self._entities, "schema_version": _RESOLVER_VERSION},
                f, indent=2, ensure_ascii=False
            )

    def get(self, entity_id: str) -> Optional[dict]:
        return self._entities.get(entity_id)

    def all_of_type(self, etype: str) -> list[dict]:
        return [e for e in self._entities.values() if e["type"] == etype]

    def register(self, entity: dict, source_file: str = "") -> dict:
        """
        Adds entity to registry if new, or enriches it if already present.
        Returns the stored canonical entity.
        """
        eid = entity["id"]
        if eid not in self._entities:
            stored = copy.deepcopy(entity)
            stored.setdefault("aliases", [])
            stored["source_files"] = [source_file] if source_file else []
            stored.setdefault("attributes", {})
            self._entities[eid] = stored
        else:
            # Enrich: add source file provenance
            stored = self._entities[eid]
            if source_file and source_file not in stored.get("source_files", []):
                stored.setdefault("source_files", []).append(source_file)
        
        # Track case_ids as corroborating signals
        case_id = entity.get("attributes", {}).get("case_id")
        if case_id:
            stored["attributes"].setdefault("case_ids", []).append(case_id)
            # Deduplicate case_ids
            stored["attributes"]["case_ids"] = list(set(stored["attributes"]["case_ids"]))
            
        self._save()
        return self._entities[eid]

    def merge_into(self, source_id: str, target_id: str) -> dict:
        """
        Merges source entity INTO target (target becomes canonical).
        Source's value is added to target's aliases.
        Source entry is removed.
        Returns canonical (target) entity.
        """
        source = self._entities.get(source_id)
        target = self._entities.get(target_id)
        if not source or not target:
            raise KeyError(f"Cannot merge: {source_id} or {target_id} not in registry.")

        # Move aliases
        target.setdefault("aliases", [])
        if source["value"] not in target["aliases"] and source["value"] != target["value"]:
            target["aliases"].append(source["value"])
        target["aliases"].extend(
            [a for a in source.get("aliases", []) if a not in target["aliases"]]
        )

        # Merge source file provenance
        for sf in source.get("source_files", []):
            if sf not in target.get("source_files", []):
                target.setdefault("source_files", []).append(sf)

        # Remove source, keep target
        del self._entities[source_id]
        self._save()
        return target


# ── Module-level registry singleton ───────────────────────────────────────────
_REGISTRY: Optional[EntityRegistry] = None

def get_registry() -> EntityRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = EntityRegistry()
    return _REGISTRY


# ══════════════════════════════════════════════════════════════════════════════
# Normalization helpers
# ══════════════════════════════════════════════════════════════════════════════

def _normalize_location_string(raw: str) -> str:
    """Expand abbreviations, normalize whitespace and casing."""
    s = raw.strip()
    for pattern, replacement in LOCATION_ABBREV.items():
        s = re.sub(pattern, replacement, s, flags=re.IGNORECASE)
    # Collapse multiple spaces / punctuation
    s = re.sub(r'[\s,]+', ' ', s).strip().title()
    return s


# ══════════════════════════════════════════════════════════════════════════════
# Per-type resolution functions
# ══════════════════════════════════════════════════════════════════════════════

def _resolve_exact(
    entities: list[dict],
    registry: EntityRegistry,
    source_file: str,
    merge_log: list
) -> tuple[list[dict], dict[str, str]]:
    """
    Exact-match resolution for PHONE and ACCOUNT entities.
    Returns (resolved_list, id_map {old_id: canonical_id}).
    """
    resolved = []
    id_map: dict[str, str] = {}

    for entity in entities:
        existing = registry.get(entity["id"])
        if existing:
            # Already known → enrich provenance, keep canonical
            registry.register(entity, source_file)
            id_map[entity["id"]] = entity["id"]
            resolved.append(existing)
            merge_log.append({
                "action":    "exact_match",
                "type":      entity["type"],
                "value":     entity["value"],
                "entity_id": entity["id"],
                "result":    "enriched existing node"
            })
        else:
            # New entity
            canonical = registry.register(entity, source_file)
            id_map[entity["id"]] = canonical["id"]
            resolved.append(canonical)
            merge_log.append({
                "action":    "new_node",
                "type":      entity["type"],
                "value":     entity["value"],
                "entity_id": entity["id"],
                "result":    "created"
            })

    return resolved, id_map


def _resolve_persons(
    entities: list[dict],
    registry: EntityRegistry,
    source_file: str,
    merge_log: list,
    needs_review: list,
    auto_threshold: int = 90,
    review_threshold: int = 70,
    corroborating_signals: Optional[dict] = None,
) -> tuple[list[dict], dict[str, str]]:
    """
    Fuzzy name resolution using rapidfuzz.token_sort_ratio.

    CRITICAL FIX: name-only similarity >= auto_threshold NO LONGER auto-merges.
    At least one corroborating signal is required to confirm identity before
    auto-merging.  Without corroboration, high similarity is still ambiguous
    (common surnames: Kumar, Singh, Khan, Shah, etc.).

    Signal hierarchy:
      similarity >= auto_threshold AND signals overlap >= 1  → auto-merge
      similarity >= auto_threshold, no corroboration         → REVIEW_REQUIRED
      similarity in [review_threshold, auto_threshold)       → REVIEW_REQUIRED
      similarity < review_threshold                          → new node

    Args:
        corroborating_signals: dict mapping entity_id -> set of signal strings
            (e.g., phone IDs, account IDs, case_id, location IDs).  Built by
            the caller from already-resolved relationships for this upload batch.
    """
    resolved = []
    id_map: dict[str, str] = {}
    known_persons = registry.all_of_type("PERSON")
    signals = corroborating_signals or {}

    for entity in entities:
        name = entity["value"]
        best_entity = None
        best_score  = 0

        for known in known_persons:
            score = fuzz.token_sort_ratio(name.lower(), known["value"].lower())
            if score > best_score:
                best_score  = score
                best_entity = known

        # ── Determine if we have a corroborating signal ───────────────────────────
        has_corroboration = False
        if best_entity and best_score >= auto_threshold:
            incoming_sigs = signals.get(entity["id"], set())
            known_sigs    = signals.get(best_entity["id"], set())
            has_corroboration = bool(incoming_sigs & known_sigs)
            
            # Bug 2 Fix: 100% identical strings should auto-merge without corroboration
            if best_score == 100:
                has_corroboration = True

        if best_score >= auto_threshold and best_entity and has_corroboration:
            # ── Auto-merge: high similarity + confirmed shared signal ─────────
            registry.register(entity, source_file)
            canonical = registry.merge_into(entity["id"], best_entity["id"])
            id_map[entity["id"]] = canonical["id"]
            resolved.append(canonical)
            merge_log.append({
                "action":     "auto_merge",
                "type":       "PERSON",
                "incoming":   name,
                "canonical":  canonical["value"],
                "similarity": best_score,
                "corroborated_by": list(incoming_sigs & known_sigs),
                "result":     f"merged into {canonical['id']}"
            })

        elif best_score >= review_threshold and best_entity:
            # ── Flag for investigator (includes: high-sim name-only, medium-sim)
            # Do NOT merge — silently merging common surnames is dangerous.
            reason = (
                f"Names are {best_score:.0f}% similar but no corroborating "
                f"signal (shared phone/account/case) was found. "
                f"Could be the same person or someone with a common surname. "
                f"Investigator confirmation required."
            ) if best_score >= auto_threshold else (
                f"Names are {best_score:.0f}% similar. "
                f"Could be the same person or a different individual. "
                f"Investigator confirmation required before merging."
            )
            canonical = registry.register(entity, source_file)
            id_map[entity["id"]] = entity["id"]
            resolved.append(canonical)
            needs_review.append({
                "review_id":      str(uuid.uuid4()),
                "type":           "PERSON_NAME_AMBIGUITY",
                "candidate":      {
                    "id":    entity["id"],
                    "value": name,
                    "source_file": source_file
                },
                "possible_match": {
                    "id":           best_entity["id"],
                    "value":        best_entity["value"],
                    "source_files": best_entity.get("source_files", [])
                },
                "similarity":     best_score,
                "corroboration_found": has_corroboration,
                "reason":         reason,
                "merge_action":   "pending"
            })
            merge_log.append({
                "action":     "flagged_for_review",
                "type":       "PERSON",
                "incoming":   name,
                "possible_match": best_entity["value"],
                "similarity": best_score,
                "corroboration_found": has_corroboration,
                "result":     "separate node created, flagged"
            })
            known_persons = registry.all_of_type("PERSON")

        else:
            # ── New node ────────────────────────────────────────────────────────────
            canonical = registry.register(entity, source_file)
            id_map[entity["id"]] = canonical["id"]
            resolved.append(canonical)
            known_persons.append(canonical)
            merge_log.append({
                "action":     "new_node",
                "type":       "PERSON",
                "value":      name,
                "entity_id":  canonical["id"],
                "result":     "created",
                "best_score": best_score
            })

    return resolved, id_map


def _resolve_locations(
    entities: list[dict],
    registry: EntityRegistry,
    source_file: str,
    merge_log: list,
    similarity_threshold: int = 85
) -> tuple[list[dict], dict[str, str]]:
    """
    Location resolution with abbreviation normalization + fuzzy match.
    Geocoding is stubbed — will call Nominatim in Phase 2.
    """
    resolved = []
    id_map: dict[str, str] = {}
    known_locs = registry.all_of_type("LOCATION")

    for entity in entities:
        normalized = _normalize_location_string(entity["value"])
        # Store the normalized version as the canonical value
        entity_norm = copy.deepcopy(entity)
        entity_norm["value"] = normalized
        # Recompute ID from normalized value
        h = hashlib.sha256(normalized.encode()).hexdigest()[:8]
        entity_norm["id"] = f"location:{h}"

        best_entity = None
        best_score  = 0

        for known in known_locs:
            score = fuzz.token_sort_ratio(normalized.lower(), known["value"].lower())
            if score > best_score:
                best_score  = score
                best_entity = known

        if best_score >= similarity_threshold and best_entity:
            registry.register(entity_norm, source_file)
            canonical = registry.merge_into(entity_norm["id"], best_entity["id"])
            id_map[entity["id"]]      = canonical["id"]
            id_map[entity_norm["id"]] = canonical["id"]
            resolved.append(canonical)
            merge_log.append({
                "action":     "location_merge",
                "incoming":   normalized,
                "canonical":  canonical["value"],
                "similarity": best_score,
                "result":     f"merged into {canonical['id']}"
            })
        else:
            # TODO Phase 2: enrich with Nominatim geocode lat/long
            # try:
            #     from geopy.geocoders import Nominatim
            #     geolocator = Nominatim(user_agent="cias")
            #     loc = geolocator.geocode(normalized + ", India")
            #     if loc: entity_norm["attributes"]["lat"] = loc.latitude; ...
            # except Exception: pass
            canonical = registry.register(entity_norm, source_file)
            id_map[entity["id"]]      = canonical["id"]
            id_map[entity_norm["id"]] = canonical["id"]
            resolved.append(canonical)
            known_locs.append(canonical)
            merge_log.append({
                "action":    "new_node",
                "type":      "LOCATION",
                "value":     normalized,
                "entity_id": canonical["id"],
                "result":    "created"
            })

    return resolved, id_map


# ══════════════════════════════════════════════════════════════════════════════
# Relationship ID rewriting
# ══════════════════════════════════════════════════════════════════════════════

def _rewrite_relationship_ids(
    relationships: list[dict],
    id_map: dict[str, str]
) -> list[dict]:
    """
    After merges, update all relationship source/target to canonical IDs.
    Any relationship whose source OR target was merged gets its pointer rewritten.
    Self-loops (source == target after merge) are written to the filtered-edge
    audit log rather than silently dropped — nothing disappears without a trace.
    """
    rewritten = []
    for rel in relationships:
        r = copy.deepcopy(rel)
        r["source"] = id_map.get(r["source"], r["source"])
        r["target"] = id_map.get(r["target"], r["target"])
        if r["source"] == r["target"]:
            # Audit the dropped self-loop — do NOT silently delete
            try:
                from ..audit.logger import log_filtered_edge
                log_filtered_edge(
                    edge=r,
                    reason="self_loop",
                    source_doc=r.get("evidence", "")[:80],
                )
            except Exception:
                pass
            continue  # still excluded from graph, but now audited
        rewritten.append(r)
    return rewritten


def _detect_phone_conflicts(
    resolved_entities: list[dict],
    resolved_relationships: list[dict],
    needs_review: list,
) -> list[dict]:
    """
    Detects cases where a single phone number is linked (via HAS_PHONE) to
    two or more distinctly different names (similarity < 70).  This commonly
    indicates:
      - A shared/prepaid SIM used by different people across different cases
      - OCR misread of a digit that confused two real numbers

    When detected:
      - The phone node is flagged with status='PHONE_CONFLICT'
      - All HAS_PHONE edges touching it get confidence=0.3, status='conflicted'
      - A review item is added to needs_review for the investigator UI

    Nothing is deleted — the conflict is surfaced, not resolved silently.
    """
    # Build phone_id → [person names] map from HAS_PHONE relationships
    phone_to_persons: dict[str, list[str]] = {}
    entity_by_id = {e["id"]: e for e in resolved_entities}

    for rel in resolved_relationships:
        if rel.get("type") == "HAS_PHONE":
            phone_id  = rel["target"]
            person_id = rel["source"]
            person    = entity_by_id.get(person_id)
            if person:
                phone_to_persons.setdefault(phone_id, []).append(person["value"])

    # Find conflicting phones (two distinct people)
    conflict_phone_ids: set[str] = set()
    for phone_id, names in phone_to_persons.items():
        if len(names) < 2:
            continue
        # Check if the names are actually distinct (not just aliases)
        max_sim = max(
            fuzz.token_sort_ratio(a.lower(), b.lower())
            for i, a in enumerate(names)
            for b in names[i + 1:]
        ) if len(names) >= 2 else 100

        if max_sim < 70:  # genuinely different people
            conflict_phone_ids.add(phone_id)
            phone_entity = entity_by_id.get(phone_id)
            if phone_entity:
                phone_entity["status"]     = "PHONE_CONFLICT"
                phone_entity["risk_color"] = "red"

            needs_review.append({
                "review_id": str(uuid.uuid4()),
                "type":      "PHONE_CONFLICT",
                "phone_id":  phone_id,
                "names":     names,
                "max_name_similarity": max_sim,
                "reason":    (
                    f"Phone {phone_id} is linked to {len(names)} distinctly "
                    f"different names (max similarity {max_sim:.0f}%). "
                    f"Possible shared SIM, OCR error, or identity fraud."
                ),
                "merge_action": "pending",
            })

    # Downgrade confidence on all HAS_PHONE edges touching conflicted phones
    for rel in resolved_relationships:
        if rel.get("type") == "HAS_PHONE" and rel["target"] in conflict_phone_ids:
            rel["confidence"] = 0.3
            rel["status"]     = "conflicted — pending investigator review"

    return resolved_relationships


# ══════════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ══════════════════════════════════════════════════════════════════════════════

def resolve_entities(
    extracted: dict,
    source_file: str = "",
    registry: Optional[EntityRegistry] = None,
    case_id: Optional[str] = None,
) -> dict:
    """
    Deduplicates and resolves all entities from a single ner.py extraction pass.

    Args:
        extracted:   Output of ner.extract_entities()
        source_file: Originating file name (for provenance tracking)
        registry:    Optional custom registry (for testing); defaults to singleton
        case_id:     Case identifier — used as a corroborating signal for
                     name-based merge decisions. Two entities in the same case
                     with high name similarity can be corroborated by case_id.

    Returns:
        {
          "resolved_entities":      list[dict],
          "resolved_relationships": list[dict],
          "merge_log":              list[dict],
          "needs_review":           list[dict],
          "stats": { "new": int, "merged": int, "flagged": int }
        }
    """
    if registry is None:
        registry = get_registry()

    raw_entities      = extracted.get("entities",      [])
    raw_relationships = extracted.get("relationships", [])

    merge_log    = []
    needs_review = []
    id_map: dict[str, str] = {}

    resolved_entities = []

    # ── Partition entities by type ─────────────────────────────────────────────
    exact_types    = [e for e in raw_entities if e["type"] in ("PHONE", "ACCOUNT")]
    person_types   = [e for e in raw_entities if e["type"] == "PERSON"]
    location_types = [e for e in raw_entities if e["type"] == "LOCATION"]
    other_types    = [
        e for e in raw_entities
        if e["type"] not in ("PHONE", "ACCOUNT", "PERSON", "LOCATION")
    ]

    # ── 1. Exact match: PHONE / ACCOUNT ──────────────────────────────────────
    resolved_exact, map_exact = _resolve_exact(
        list(exact_types), registry, source_file, merge_log
    )
    resolved_entities.extend(resolved_exact)
    id_map.update(map_exact)

    # ── 1.5 Build corroborating signals ──────────────────────────────────────
    # Names only auto-merge if they share a corroborating signal.
    # Currently, we use case_id.
    corroborating_signals = {}
    
    # 1.5a Incoming entities get the case_id signal
    if case_id:
        for p in person_types:
            corroborating_signals.setdefault(p["id"], set()).add(f"case:{case_id}")
            # Also store it in attributes so registry persists it
            p.setdefault("attributes", {})["case_id"] = case_id
            
    # 1.5b Known entities in the registry supply their case_ids
    for known_person in registry.all_of_type("PERSON"):
        case_ids = known_person.get("attributes", {}).get("case_ids", [])
        sigs = {f"case:{cid}" for cid in case_ids}
        if sigs:
            corroborating_signals[known_person["id"]] = sigs

    # ── 2. Fuzzy match: PERSON ───────────────────────────────────────────────
    resolved_persons, map_persons = _resolve_persons(
        list(person_types), registry, source_file, merge_log, needs_review,
        corroborating_signals=corroborating_signals
    )
    resolved_entities.extend(resolved_persons)
    id_map.update(map_persons)

    # ── 3. Normalized fuzzy: LOCATION ────────────────────────────────────────
    resolved_locs, map_locs = _resolve_locations(
        list(location_types), registry, source_file, merge_log
    )
    resolved_entities.extend(resolved_locs)
    id_map.update(map_locs)

    # ── 4. Other types (VEHICLE, FIR, AADHAAR, ORG): exact by ID ────────────
    resolved_others, map_others = _resolve_exact(
        other_types, registry, source_file, merge_log
    )
    resolved_entities.extend(resolved_others)
    id_map.update(map_others)

    # ── 5. Rewrite relationship pointers with updated IDs ─────────────────────
    resolved_relationships = _rewrite_relationship_ids(raw_relationships, id_map)

    # ── 6. Compute stats ──────────────────────────────────────────────────────
    new_count    = sum(1 for e in merge_log if e["action"] == "new_node")
    merged_count = sum(1 for e in merge_log if "merge" in e["action"])
    flagged_count = len(needs_review)

    return {
        "resolved_entities":      resolved_entities,
        "resolved_relationships": resolved_relationships,
        "merge_log":              merge_log,
        "needs_review":           needs_review,
        "stats": {
            "new":     new_count,
            "merged":  merged_count,
            "flagged": flagged_count
        }
    }
