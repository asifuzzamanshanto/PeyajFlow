from alembic import context

from app.database import database_engine
from app.main import metadata


def run(connection=None):
    if connection is None:
        context.configure(dialect_name="postgresql", target_metadata=metadata)
    else:
        context.configure(connection=connection, target_metadata=metadata)
    with context.begin_transaction():
        context.run_migrations()


provided = context.config.attributes.get("connection")
if provided is not None:
    run(provided)
elif context.is_offline_mode():
    run()
else:
    engine = database_engine()
    if engine is None:
        raise RuntimeError("Set DATABASE_URL before running migrations")
    try:
        with engine.connect() as connection:
            run(connection)
    finally:
        engine.dispose()
