from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DATABASE_", extra="ignore")

    url: str = "postgresql+asyncpg://codeforge:codeforge@localhost:5432/codeforge"
    sync_url: str = "postgresql://codeforge:codeforge@localhost:5432/codeforge"


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_", extra="ignore")

    url: str = "redis://localhost:6379/0"


class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    default_simple_model: str = "llama3:8b"
    default_complex_model: str = "gpt-4"
    complexity_simple_threshold: float = 0.3
    complexity_complex_threshold: float = 0.7


class SandboxSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SANDBOX_", extra="ignore")

    image: str = "codeforge-sandbox-python:latest"
    timeout_seconds: int = 30
    memory_limit_mb: int = 512
    cpu_limit: float = 1.0
    network_disabled: bool = True


class ObservabilitySettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "codeforge-backend"
    log_level: str = "INFO"
    log_format: str = "json"


class ServerSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:3000"
    secret_key: str = "change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://codeforge:codeforge@localhost:5432/codeforge"
    database_sync_url: str = "postgresql://codeforge:codeforge@localhost:5432/codeforge"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    default_simple_model: str = "llama3:8b"
    default_complex_model: str = "gpt-4"
    complexity_simple_threshold: float = 0.3
    complexity_complex_threshold: float = 0.7

    # Research / Web Search
    tavily_api_key: Optional[str] = None
    serp_api_key: Optional[str] = None
    research_max_queries: int = 5
    research_enabled: bool = True

    # Sandbox
    sandbox_image: str = "codeforge-sandbox-python:latest"
    sandbox_timeout_seconds: int = 30
    sandbox_memory_limit_mb: int = 512
    sandbox_cpu_limit: float = 1.0
    sandbox_network_disabled: bool = True
    max_repair_retries: int = 3
    docker_host: str = "unix:///var/run/docker.sock"

    # Observability
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "codeforge-backend"
    log_level: str = "INFO"
    log_format: str = "json"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:3000"
    secret_key: str = "change-me-in-production"

    # Agent / Conversation
    agent_model: str = "openai/gpt-4o-mini"
    agent_max_iterations: int = 25
    agent_workspace_root: str = "/tmp/codeforge-workspace"

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith(("postgresql", "sqlite")):
            raise ValueError("DATABASE_URL must start with postgresql or sqlite")
        return v

    @property
    def HOST(self) -> str:  # noqa: N802
        return self.host

    @property
    def PORT(self) -> int:  # noqa: N802
        return self.port

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
