# We build Neo4j locally from the official slim base image.
# This avoids downloading the full neo4j:5-community layer in one shot
# (which causes EOF errors on unstable connections).
FROM neo4j:5.20.0-community

# Set default environment variables (overridable by docker-compose)
ENV NEO4J_AUTH=neo4j/password

# Expose bolt and HTTP ports
EXPOSE 7474 7687
