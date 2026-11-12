from alembic import context

from app.database import database_engine
from app.main import metadata

engine = database_engine()
if engine is None:
    raise RuntimeError("Set DATABASE_URL before running migrations")

try:
    if context.is_offline_mode():
        context.configure(dialect_name=engine.dialect.name, target_metadata=metadata)
        with context.begin_transaction():
            context.run_migrations()
    else:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=metadata)
            with context.begin_transaction():
                context.run_migrations()
finally:
    engine.dispose()
