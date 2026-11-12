from datetime import UTC, datetime, timedelta
from hashlib import sha256

from fastapi import HTTPException
from sqlalchemy import Column, DateTime, Integer, String, Table, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.database import metadata

buckets = Table(
    "rate_buckets",
    metadata,
    Column("key", String(64), primary_key=True),
    Column("window_start", DateTime(timezone=True), primary_key=True, index=True),
    Column("hits", Integer, nullable=False),
)


def enforce(
    db: Session, scope: str, identifier: str, *, limit: int, seconds: int
) -> None:
    instant = int(datetime.now(UTC).timestamp())
    start = instant - instant % seconds
    key = sha256(f"{scope}\0{identifier}".encode()).hexdigest()
    allowed = db.scalar(
        pg_insert(buckets)
        .values(
            key=key,
            window_start=datetime.fromtimestamp(start, UTC),
            hits=1,
        )
        .on_conflict_do_update(
            index_elements=[buckets.c.key, buckets.c.window_start],
            set_={"hits": buckets.c.hits + 1},
            where=buckets.c.hits < limit,
        )
        .returning(buckets.c.hits)
    )
    db.commit()
    if allowed is None:
        raise HTTPException(
            429, "rate_limited", headers={"Retry-After": str(start + seconds - instant)}
        )


def prune(engine) -> None:
    with Session(engine) as db, db.begin():
        db.execute(
            delete(buckets).where(
                buckets.c.window_start < datetime.now(UTC) - timedelta(days=1)
            )
        )
