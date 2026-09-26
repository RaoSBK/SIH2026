from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@postgres:5432/criminal_intel"

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    jwt_secret_key: str = "supersecretkey123_cias_veritas"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
