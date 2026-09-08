from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@postgres:5432/criminal_intel"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    jwt_secret_key: str            # no default — must come from env, fail loudly if missing
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    class Config:
        env_file = ".env"

settings = Settings()
