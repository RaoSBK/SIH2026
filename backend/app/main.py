import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.router import api_router
from .database.postgres import init_db

logger = logging.getLogger(__name__)

# Initialize relational DB schema (SQLite / PostgreSQL)
init_db()

app = FastAPI(title="CIAS ML Backend")

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Local dev — restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount central API router containing all domain endpoints
app.include_router(api_router)

@app.get("/")
def read_root():
    return {"status": "ok", "service": "CIAS ML Backend"}
