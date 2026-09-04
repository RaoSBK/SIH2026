import os
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def insert_graph_data(nodes: list[dict], links: list[dict], file_name: str = "unknown", case_id: str = None):
    """
    Persists resolved entities and relationships into Neo4j.
    Also links them to a Document node for clean re-ingestion.
    """
    if not nodes and not links:
        return

    with driver.session() as session:
        # Insert Document Node
        session.run(
            "MERGE (d:Document {file_name: $file_name, case_id: $case_id})",
            file_name=file_name, case_id=case_id or "unknown"
        )

        # Insert Nodes
        for node in nodes:
            # We use MERGE so we don't duplicate nodes that already exist in Neo4j
            query = (
                f"MERGE (n:{node['type']} {{id: $id}}) "
                "SET n.value = $value, "
                "    n.confidence = $confidence, "
                "    n += $attributes"
            )
            session.run(
                query,
                id=node["id"],
                value=node["value"],
                confidence=node.get("confidence", 1.0),
                attributes=node.get("attributes", {})
            )
            
            # Link entity to the Document
            session.run(
                "MATCH (n {id: $id}), (d:Document {file_name: $file_name, case_id: $case_id}) "
                "MERGE (n)-[:EXTRACTED_FROM]->(d)",
                id=node["id"], file_name=file_name, case_id=case_id or "unknown"
            )
            
            # If there are aliases, set them (useful for PERSON nodes)
            if node.get("aliases"):
                session.run(
                    f"MATCH (n:{node['type']} {{id: $id}}) SET n.aliases = $aliases",
                    id=node["id"],
                    aliases=node["aliases"]
                )
                
            # Update source_files provenance
            if node.get("source_files"):
                session.run(
                    f"MATCH (n:{node['type']} {{id: $id}}) "
                    "SET n.source_files = coalesce(n.source_files, []) + [x IN $source_files WHERE NOT x IN coalesce(n.source_files, [])]",
                    id=node["id"],
                    source_files=node["source_files"]
                )

        # Insert Relationships
        skipped = []
        for link in links:
            # Cypher requires relationship types to be static in the query string
            rel_type = link["type"].replace(" ", "_").upper()
            query = (
                "MATCH (source {id: $source_id}) "
                "MATCH (target {id: $target_id}) "
                f"MERGE (source)-[r:{rel_type}]->(target) "
                "SET r.confidence = $confidence, "
                "    r.status = $status, "
                "    r.evidence = $evidence, "
                "    r += $attributes"
            )
            result = session.run(
                query,
                source_id=link["source"],
                target_id=link["target"],
                confidence=link.get("confidence", 1.0),
                status=link.get("status", "confirmed"),
                evidence=link.get("evidence", ""),
                attributes=link.get("attributes", {})
            )
            summary = result.consume()
            if summary.counters.relationships_created == 0 and summary.counters.properties_set == 0:
                skipped.append((link["source"], link["target"], rel_type))
                
        if skipped:
            print(f"[insert_graph_data] WARNING: {len(skipped)}/{len(links)} "
                  f"relationships had no matching source/target node id:")
            for s, t, rt in skipped[:15]:
                print(f"    {s} --{rt}--> {t}")

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

