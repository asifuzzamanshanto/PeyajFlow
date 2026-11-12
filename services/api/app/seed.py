from sqlalchemy.orm import Session

from app.auth import demo_enabled, seed_demo
from app.database import database_engine


def main() -> None:
    if not demo_enabled():
        raise SystemExit(
            "Set APP_ENV=development and DEMO_MODE=true to seed fictional accounts."
        )
    engine = database_engine()
    if engine is None:
        raise SystemExit("Set DATABASE_URL before seeding.")
    try:
        with Session(engine) as db:
            seed_demo(db)
            db.commit()
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
