from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from secondbrain.config import settings


def build_database_url(
    database: str | None = None,
    host: str | None = None,
    port: int | None = None,
) -> str:
    return (
        f"postgresql+psycopg://"
        f"{settings.postgres_user}:"
        f"{settings.postgres_password}@"
        f"{host if host is not None else settings.postgres_host}:"
        f"{port if port is not None else settings.postgres_port}/"
        f"{database if database is not None else settings.postgres_db}"
    )


DATABASE_URL = build_database_url()


engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass
