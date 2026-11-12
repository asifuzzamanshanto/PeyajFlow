import os
from pathlib import Path

from alembic.config import Config
from sqlalchemy import Engine, MetaData, create_engine, make_url

API_ROOT = Path(__file__).resolve().parents[1]
metadata = MetaData()


def alembic_config() -> Config:
    return Config(str(API_ROOT / "alembic.ini"))


def database_engine() -> Engine | None:
    value = os.environ.get("DATABASE_URL")
    if not value:
        return None

    url = make_url(value)
    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+psycopg")
    if url.drivername != "postgresql+psycopg":
        raise ValueError("DATABASE_URL must use PostgreSQL with psycopg")

    return create_engine(
        url,
        connect_args={"connect_timeout": 3, "options": "-c statement_timeout=3000"},
        pool_pre_ping=True,
        pool_timeout=3,
        hide_parameters=True,
    )
