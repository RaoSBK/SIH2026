import os
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def insert_graph_data(nodes: list[dict], links: list[dict]):
    """
    Persists resolved entities and relationships into Neo4j.
    """
    if not nodes and not links:
        return

    with driver.session() as session:
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
            session.run(
                query,
                source_id=link["source"],
                target_id=link["target"],
                confidence=link.get("confidence", 1.0),
                status=link.get("status", "confirmed"),
                evidence=link.get("evidence", ""),
                attributes=link.get("attributes", {})
            )
