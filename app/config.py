"""
Configuration settings for the application, including Neo4j connection details,
JWT auth settings, and application environment settings.
This module uses Pydantic's BaseSettings to load settings from environment variables or a .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Neo4j
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str

    # JWT
    jwt_secret_key: str
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
