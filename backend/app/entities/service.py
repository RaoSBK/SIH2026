# -*- coding: utf-8 -*-

from backend.app.database.neo4j import driver as neo4j_driver
from backend.app.utils.exceptions import not_found

def get_entity_detail(entity_id: str) -> dict:
    """
    Queries neo4j.driver directly to return the node's own properties
    plus its direct relationships.
    """
    try:
        with neo4j_driver.session() as session:
            # Match the node
            node_result = session.run(
                "MATCH (n {id: $entity_id}) "
                "RETURN properties(n) AS properties, labels(n) AS labels",
                entity_id=entity_id
            ).single()

            if not node_result:
                raise not_found(f"Entity {entity_id} not found")

            properties = node_result["properties"]
            labels = node_result["labels"]

            # Match relationships where this node is either source or target
            # Note: We filter out EXTRACTED_FROM to focus on entity-entity relationships,
            # or we can include them if we want to show document provenance.
            rels_result = session.run(
                "MATCH (a {id: $entity_id})-[r]-(b) "
                "RETURN startNode(r).id AS source, endNode(r).id AS target, "
                "type(r) AS type, properties(r) AS properties",
                entity_id=entity_id
            )
            
            relationships = []
            for record in rels_result:
                relationships.append({
                    "source": record["source"],
                    "target": record["target"],
                    "type": record["type"],
                    "properties": record["properties"]
                })

        return {
            "id": entity_id,
            "properties": properties,
            "labels": labels,
            "relationships": relationships
        }
    except Exception as e:
        if isinstance(e, not_found().__class__):
            raise e
        raise Exception(f"Failed to fetch entity details: {e}")
