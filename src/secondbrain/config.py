import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


class Settings:
    def __init__(self) -> None:
        self.app_name: str = os.getenv("APP_NAME", "SecondBrain")
        self.environment: str = os.getenv("ENVIRONMENT", "development")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

        self.postgres_db: str = os.getenv("POSTGRES_DB", "secondbrain")
        self.postgres_user: str = os.getenv("POSTGRES_USER", "secondbrain")
        self.postgres_password: str = os.getenv("POSTGRES_PASSWORD", "")
        self.postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
        self.postgres_port: int = _get_int("POSTGRES_PORT", 5432)
        self.postgres_test_db: str = os.getenv(
            "POSTGRES_TEST_DB",
            f"{os.getenv('POSTGRES_DB', 'secondbrain')}_test",
        )

        self.jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
        self.jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_access_token_expire_minutes: int = _get_int(
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30
        )

        self.document_storage_path: str = os.getenv(
            "DOCUMENT_STORAGE_PATH",
            "storage/documents",
        )
        self.max_upload_size_mb: int = _get_int("MAX_UPLOAD_SIZE_MB", 20)
        self.max_request_size_mb: int = _get_int("MAX_REQUEST_SIZE_MB", 25)
        self.process_on_upload: bool = _get_bool("PROCESS_ON_UPLOAD", True)

        self.chunk_size: int = _get_int("CHUNK_SIZE", 1000)
        self.chunk_overlap: int = _get_int("CHUNK_OVERLAP", 200)

        self.embedding_provider: str = os.getenv(
            "EMBEDDING_PROVIDER", "hashing"
        ).lower()
        self.embedding_model: str = os.getenv(
            "EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"
        )
        self.embedding_dim: int = _get_int("EMBEDDING_DIM", 384)

        self.llm_provider: str = os.getenv("LLM_PROVIDER", "extractive").lower()
        self.llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        self.openai_base_url: str = os.getenv(
            "OPENAI_BASE_URL", "https://api.openai.com/v1"
        )
        self.groq_api_key: str = os.getenv("GROQ_API_KEY", "")
        self.groq_base_url: str = os.getenv(
            "GROQ_BASE_URL", "https://api.groq.com/openai/v1"
        )
        self.provider_timeout_seconds: int = _get_int(
            "PROVIDER_TIMEOUT_SECONDS", 30
        )

        self.retrieval_top_k: int = _get_int("RETRIEVAL_TOP_K", 5)
        self.retrieval_min_similarity: float = float(
            os.getenv("RETRIEVAL_MIN_SIMILARITY", "0.0")
        )
        self.rag_max_context_chars: int = _get_int("RAG_MAX_CONTEXT_CHARS", 6000)

        self.cors_origins: list[str] = [
            origin.strip()
            for origin in os.getenv("CORS_ORIGINS", "").split(",")
            if origin.strip()
        ]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def max_request_size_bytes(self) -> int:
        return self.max_request_size_mb * 1024 * 1024

    def validate(self) -> None:
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                "CHUNK_OVERLAP must be smaller than CHUNK_SIZE"
            )
        if self.embedding_dim <= 0:
            raise ValueError("EMBEDDING_DIM must be positive")
        if self.embedding_provider == "openai" and not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai"
            )
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when LLM_PROVIDER=openai"
            )
        if self.llm_provider == "groq" and not self.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY is required when LLM_PROVIDER=groq"
            )
        if self.environment != "test" and not self.jwt_secret_key:
            raise ValueError(
                "JWT_SECRET_KEY must be set. Generate one with: "
                "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
