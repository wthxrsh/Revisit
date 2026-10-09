import os

from dotenv import load_dotenv


load_dotenv()


class Settings:
    app_name: str = os.getenv("APP_NAME", "SecondBrain")
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    postgres_db: str = os.getenv("POSTGRES_DB", "secondbrain")
    postgres_user: str = os.getenv("POSTGRES_USER", "secondbrain")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "")
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_expire_minutes: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    document_storage_path: str = os.getenv(
        "DOCUMENT_STORAGE_PATH",
        "storage/documents",
    )


settings = Settings()