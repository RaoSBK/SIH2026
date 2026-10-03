# Deployment Architecture & Topology

VERITAS supports both local Docker Compose orchestration for air-gapped forensic environments and cloud deployment across Vercel, Render, Supabase, and Neo4j Aura.

Source Code: [`docker-compose.yml`](file:///d:/SIH2026/docker-compose.yml), [`infrastructure/`](file:///d:/SIH2026/infrastructure/)

```
                    ┌─────────────────────────┐
                    │  Vercel Cloud Platform  │
                    │  (Next.js Frontend UI)  │
                    └────────────┬────────────┘
                                 │ HTTPS / WebSockets
                                 ▼
                    ┌─────────────────────────┐
                    │  Render Cloud Platform  │
                    │  (FastAPI Backend App)  │
                    └────┬───────────────┬────┘
                         │               │
      Bolt Protocol (7687)│               │ SQL (5432)
                         ▼               ▼
        ┌──────────────────┐           ┌──────────────────┐
        │ Neo4j Aura Cloud │           │  Supabase Cloud  │
        │ (Graph Database) │           │ (PostgreSQL DB)  │
        └──────────────────┘           └──────────────────┘
```

## Cloud Topology Stack

1. **Frontend Host (Vercel)**: Next.js Single Page Application served via global CDN edge nodes with HTTPS termination.
2. **Backend Application Host (Render)**: Python 3.12 FastAPI container running under Uvicorn with auto-scaling process workers.
3. **Graph Database Host (Neo4j AuraDB)**: Managed enterprise Neo4j cloud instance running Neo4j 5.x with APOC plugin over encrypted Bolt (`bolt+s://`) protocol.
4. **Relational Database Host (Supabase)**: Managed PostgreSQL 15 database instance hosting case management tables, user credentials, and evidence file storage buckets.

## Local Docker Compose Setup

For air-gapped law enforcement installations, the full stack runs locally via `docker-compose`:

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - POSTGRES_SERVER=postgres
  frontend:
    build:
      context: ./frontend
      dockerfile: ../infrastructure/docker/frontend.Dockerfile
    ports:
      - "3000:80"
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
  neo4j:
    build:
      context: ./infrastructure/docker
      dockerfile: neo4j.Dockerfile
    ports:
      - "7474:7474"
      - "7687:7687"
```

### Execution Command
```bash
docker-compose up --build -d
```
