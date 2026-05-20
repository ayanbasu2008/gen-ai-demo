import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Production-grade application settings."""

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"

    # Kafka
    KAFKA_BOOTSTRAP: str = os.getenv("KAFKA_BOOTSTRAP", "localhost:29092")
    KAFKA_SASL_MECHANISM: Optional[str] = os.getenv("KAFKA_SASL_MECHANISM")
    KAFKA_SASL_USERNAME: Optional[str] = os.getenv("KAFKA_SASL_USERNAME")
    KAFKA_SASL_PASSWORD: Optional[str] = os.getenv("KAFKA_SASL_PASSWORD")
    KAFKA_SECURITY_PROTOCOL: str = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
    KAFKA_SSL_CAFILE: Optional[str] = os.getenv("KAFKA_SSL_CAFILE")

    # Database
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "agentpass")
    POSTGRES_URI: str = os.getenv(
        "POSTGRES_URI", "postgresql://agent:agentpass@localhost:5432/agents"
    )

    # API Security
    API_KEY: str = os.getenv("API_KEY", "dev-api-key")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-key")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # Monitoring
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    PROMETHEUS_PORT: int = int(os.getenv("PROMETHEUS_PORT", 9090))
    GRAFANA_PASSWORD: str = os.getenv("GRAFANA_PASSWORD", "admin")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")

    # Retry Configuration
    KAFKA_RETRY_MAX_ATTEMPTS: int = int(os.getenv("KAFKA_RETRY_MAX_ATTEMPTS", "5"))
    KAFKA_RETRY_DELAY_SECONDS: int = int(os.getenv("KAFKA_RETRY_DELAY_SECONDS", "2"))

    model_config = ConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
