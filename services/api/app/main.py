from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from enum import StrEnum

from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import FastAPI, Response
from pydantic import BaseModel
from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.database import alembic_config, database_engine


class DatabaseStatus(StrEnum):
    READY = "ready"
    UNCONFIGURED = "unconfigured"
    UNREACHABLE = "unreachable"
    MIGRATION_REQUIRED = "migration_required"


class Liveness(BaseModel):
    status: str = "ok"


class Readiness(BaseModel):
    database: DatabaseStatus


def check_database(
    engine: Engine | None, expected_heads: frozenset[str]
) -> DatabaseStatus:
    if engine is None:
        return DatabaseStatus.UNCONFIGURED

    try:
        with engine.connect() as connection:
            current_heads = frozenset(
                MigrationContext.configure(connection).get_current_heads()
            )
    except SQLAlchemyError:
        return DatabaseStatus.UNREACHABLE

    if current_heads != expected_heads:
        return DatabaseStatus.MIGRATION_REQUIRED
    return DatabaseStatus.READY


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    heads = frozenset(ScriptDirectory.from_config(alembic_config()).get_heads())
    if len(heads) != 1:
        raise RuntimeError("PeyajFlow requires exactly one Alembic head")

    engine = database_engine()
    application.state.database_engine = engine
    application.state.migration_heads = heads
    try:
        yield
    finally:
        if engine is not None:
            engine.dispose()


app = FastAPI(title="PeyajFlow API", version="0.1.0", lifespan=lifespan)


@app.get("/health/live", response_model=Liveness, tags=["Health"])
def live() -> Liveness:
    return Liveness()


@app.get(
    "/health/ready",
    response_model=Readiness,
    responses={
        503: {"model": Readiness, "description": "Database unavailable or out of date"}
    },
    tags=["Health"],
)
def ready(response: Response) -> Readiness:
    database = check_database(app.state.database_engine, app.state.migration_heads)
    if database != DatabaseStatus.READY:
        response.status_code = 503
    return Readiness(database=database)
