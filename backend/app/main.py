import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.router import router
from backend.app.database.postgres import init_db, Base, engine, SessionLocal

logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    try:
        init_db()
        Base.metadata.create_all(bind=engine)
        
        # Initialize Neo4j schema indexes and constraints
        from backend.app.database.neo4j import init_neo4j_schema
        init_neo4j_schema()
        
        # Seed default user rao.a
        from backend.app.users.models import User
        from backend.app.auth.authentication import hash_password
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == "rao.a").first()
            if not user:
                new_user = User(
                    username="rao.a",
                    hashed_password=hash_password("veritas"),
                    role="investigator",
                    full_name="Inspector Arjun Rao"
                )
                db.add(new_user)
                db.commit()
        except Exception as e:
            logger.warning(f"Default user seeding skipped: {e}")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Startup DB init warning: {e}")
    
    yield
    
    # Shutdown tasks (if any)

app = FastAPI(title="CIAS ML Backend", lifespan=lifespan)
app.include_router(router)

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "service": "CIAS ML Backend"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
