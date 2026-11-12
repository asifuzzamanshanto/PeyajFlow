from alembic import command

from app.database import alembic_config, database_engine

LOCK = 193719284


def main() -> None:
    engine = database_engine()
    if engine is None:
        raise SystemExit("Set DATABASE_URL before migrating.")
    try:
        with engine.connect() as connection:
            acquired = connection.exec_driver_sql(
                "select pg_try_advisory_lock(%s)", (LOCK,)
            ).scalar()
            connection.commit()
            if not acquired:
                raise SystemExit(
                    "Another PeyajFlow migration is running. Retry after it finishes."
                )
            try:
                connection.exec_driver_sql("set statement_timeout = '60s'")
                connection.commit()
                config = alembic_config()
                config.attributes["connection"] = connection
                command.upgrade(config, "head")
            finally:
                connection.rollback()
                connection.exec_driver_sql("select pg_advisory_unlock(%s)", (LOCK,))
                connection.commit()
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
