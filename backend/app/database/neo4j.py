import os
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD),
    max_connection_pool_size=50,
    max_connection_lifetime=3600,
    keep_alive=True
)

def init_neo4j_schema():
    """Initializes Neo4j constraints and indexes if missing."""
    constraints_and_indexes = [
        "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE",
        "CREATE INDEX doc_case_idx IF NOT EXISTS FOR (d:Document) ON (d.case_id)",
        "CREATE INDEX doc_file_idx IF NOT EXISTS FOR (d:Document) ON (d.file_name)",
        "CREATE INDEX entity_phone_idx IF NOT EXISTS FOR (n:Entity) ON (n.phone)",
        "CREATE INDEX entity_val_idx IF NOT EXISTS FOR (n:Entity) ON (n.value)",
    ]
    try:
        with driver.session() as session:
            for stmt in constraints_and_indexes:
                try:
                    session.run(stmt)
                except Exception:
                    pass
    except Exception as e:
        print(f"[Neo4j] Schema init warning: {e}")

def insert_graph_data(nodes: list[dict], links: list[dict], file_name: str = "unknown", case_id: str = None):
    """
    Persists resolved entities and relationships into Neo4j using batched UNWIND queries.
    Also links them to a Document node for clean re-ingestion.
    """
    if not nodes and not links:
        return

    cid = case_id or "unknown"
    with driver.session() as session:
        # 1. Merge Document Node
        session.run(
            "MERGE (d:Document {file_name: $file_name, case_id: $case_id})",
            file_name=file_name, case_id=cid
        )

        # 2. Batch Insert Nodes via UNWIND
        if nodes:
            formatted_nodes = []
            for n in nodes:
                node_type = str(n.get("type") or n.get("label") or "Entity").capitalize()
                if node_type == "Org": node_type = "Organization"
                formatted_nodes.append({
                    "id": n["id"],
                    "value": n.get("value", n["id"]),
                    "type": node_type,
                    "confidence": float(n.get("confidence", 1.0)),
                    "attributes": n.get("attributes", {}),
                    "aliases": n.get("aliases", []),
                    "source_files": n.get("source_files", [file_name] if file_name != "unknown" else [])
                })

            batch_node_query = (
                "UNWIND $nodes AS item "
                "MERGE (n:Entity {id: item.id}) "
                "SET n.value = item.value, "
                "    n.confidence = item.confidence, "
                "    n.case_id = $case_id, "
                "    n += item.attributes, "
                "    n.aliases = CASE WHEN size(item.aliases) > 0 THEN item.aliases ELSE n.aliases END, "
                "    n.source_files = coalesce(n.source_files, []) + [x IN item.source_files WHERE NOT x IN coalesce(n.source_files, [])] "
                "WITH n, item "
                "CALL apoc.create.addLabels(n, [item.type]) YIELD node AS updated_node "
                "WITH updated_node AS n "
                "MATCH (d:Document {file_name: $file_name, case_id: $case_id}) "
                "MERGE (n)-[:EXTRACTED_FROM]->(d)"
            )
            session.run(batch_node_query, nodes=formatted_nodes, file_name=file_name, case_id=cid)

        # 3. Batch Insert Relationships via UNWIND grouped by rel_type
        if links:
            links_by_type = {}
            for link in links:
                rel_type = str(link.get("type") or "LINK").replace(" ", "_").upper()
                if rel_type not in links_by_type:
                    links_by_type[rel_type] = []
                links_by_type[rel_type].append({
                    "source": link["source"],
                    "target": link["target"],
                    "confidence": float(link.get("confidence", 1.0)),
                    "status": link.get("status", "confirmed"),
                    "evidence": link.get("evidence", ""),
                    "attributes": link.get("attributes", {})
                })

            for rel_type, link_batch in links_by_type.items():
                batch_rel_query = (
                    "UNWIND $batch AS item "
                    "MATCH (source {id: item.source}) "
                    "MATCH (target {id: item.target}) "
                    f"MERGE (source)-[r:{rel_type}]->(target) "
                    "SET r.confidence = item.confidence, "
                    "    r.status = item.status, "
                    "    r.evidence = item.evidence, "
                    "    r += item.attributes"
                )
                session.run(batch_rel_query, batch=link_batch)

def delete_entities_by_source(file_name: str, case_id: str = None):
    """
    Deletes all entities that were extracted ONLY from this document.
    Entities extracted from multiple documents will have their EXTRACTED_FROM link removed,
    and if they have no more EXTRACTED_FROM links, they are deleted.
    """
    with driver.session() as session:
        # First, remove the EXTRACTED_FROM edges for this document
        session.run(
            "MATCH (n)-[r:EXTRACTED_FROM]->(d:Document {file_name: $file_name, case_id: $case_id}) "
            "DELETE r",
            file_name=file_name, case_id=case_id or "unknown"
        )
        
        # Then, delete any nodes that are no longer extracted from ANY document
        # (excluding Document nodes themselves)
        session.run(
            "MATCH (n) "
            "WHERE NOT n:Document AND NOT (n)-[:EXTRACTED_FROM]->(:Document) "
            "DETACH DELETE n"
        )
        
        # Finally, delete the Document node itself
        session.run(
            "MATCH (d:Document {file_name: $file_name, case_id: $case_id}) "
            "DELETE d",
            file_name=file_name, case_id=case_id or "unknown"
        )


def merge_nodes_in_neo4j(source_id: str, target_id: str):
    """
    Merges source entity node INTO target entity node in Neo4j.
    Re-links relationships and removes the source node.
    """
    if not source_id or not target_id or source_id == target_id:
        return
    try:
        with driver.session() as session:
            # Transfer aliases & source_files
            session.run(
                "MATCH (s {id: $source_id}), (t {id: $target_id}) "
                "SET t.aliases = coalesce(t.aliases, []) + [s.value] + coalesce(s.aliases, []), "
                "    t.source_files = coalesce(t.source_files, []) + [x IN coalesce(s.source_files, []) WHERE NOT x IN coalesce(t.source_files, [])]",
                source_id=source_id, target_id=target_id
            )
            # Re-link outgoing relationships
            session.run(
                "MATCH (s {id: $source_id})-[r]->(o) "
                "WHERE o.id <> $target_id AND type(r) <> 'EXTRACTED_FROM' "
                "MATCH (t {id: $target_id}) "
                "MERGE (t)-[r2:KNOWS]->(o) SET r2 = properties(r) "
                "DELETE r",
                source_id=source_id, target_id=target_id
            )
            # Re-link incoming relationships
            session.run(
                "MATCH (o)-[r]->(s {id: $source_id}) "
                "WHERE o.id <> $target_id AND type(r) <> 'EXTRACTED_FROM' "
                "MATCH (t {id: $target_id}) "
                "MERGE (o)-[r2:KNOWS]->(t) SET r2 = properties(r) "
                "DELETE r",
                source_id=source_id, target_id=target_id
            )
            # Detach delete source node
            session.run(
                "MATCH (s {id: $source_id}) DETACH DELETE s",
                source_id=source_id
            )
    except Exception as e:
        print(f"[Neo4j] Graph merge notice for {source_id} -> {target_id}: {e}")

