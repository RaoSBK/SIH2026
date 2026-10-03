# Graph Analytics & Network Topology

VERITAS uses NetworkX graph analytics algorithms to compute topological centrality, identify criminal key figures (kingpins, brokers, couriers), detect covert communities, and trace shortest communication/financial paths.

## Analytics Service Implementation

Source Code: [`graph/services/analytics_service.py`](file:///d:/SIH2026/graph/services/analytics_service.py), [`backend/app/api/analytics.py`](file:///d:/SIH2026/backend/app/api/analytics.py)

## Key Network Metrics Computed

### 1. PageRank (Top Influencers / Kingpins)
- **Algorithm**: `networkx.pagerank()`
- **Purpose**: Identifies central entities that hold high structural influence across the network, even if they communicate through intermediaries.
- **API Response Key**: `pagerank`, `top_influencers`

### 2. Betweenness Centrality (Network Bridges / Brokers)
- **Algorithm**: `networkx.betweenness_centrality()`
- **Purpose**: Detects "bridge" entities (couriers, handlers, middle-men) that sit on the shortest paths between different criminal subnetworks.
- **API Response Key**: `betweenness`, `top_bridges`

### 3. Community Detection (Subnetwork Clustering)
- **Algorithm**: Louvain / Clauset-Newman-Moore Community Detection (`networkx.community.greedy_modularity_communities()`)
- **Purpose**: Partitions the global network graph into distinct functional sub-gangs or modules (e.g., logistics cell, financial laundering cell).
- **API Response Key**: `communities`

### 4. Shortest Path Tracing
- **Algorithm**: `networkx.shortest_path()`
- **Purpose**: Traces the exact chain of connections (calls, transfers, meetings) linking any suspect A to suspect B.
- **Endpoint**: `GET /api/analytics/shortest-path?case_id={id}&source={A}&target={B}`

## Integration with API

Analytics are executed dynamically on case graphs via `GET /api/cases/{case_id}/analytics` or on arbitrary graph payloads via `POST /api/analytics/run`.
