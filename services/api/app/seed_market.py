import csv
from datetime import timedelta
from io import StringIO

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import (
    Profile,
    Role,
    demo_enabled,
    demo_id,
    seed_demo,
    showcase_access_key,
)
from app.database import database_engine
from app.lots import today
from app.market_data import (
    CSV_FIELDS,
    ImportInput,
    ReviewImport,
    import_csv,
    imports,
    review_batch,
)


def main() -> None:
    if not (demo_enabled() or showcase_access_key()):
        raise SystemExit("Synthetic data requires explicit demo mode.")
    engine = database_engine()
    if engine is None:
        raise SystemExit("Set DATABASE_URL first.")
    monday = today() - timedelta(days=today().weekday())
    label = f"Synthetic weekly farmgate sample through {monday}"
    actor = Profile(
        user_id=demo_id("user", "admin"),
        membership_id=demo_id("membership", "admin"),
        organization_id=demo_id("organization", "admin"),
        organization="Operations desk",
        name="Operations desk",
        district="Dhaka",
        language="bn",
        role=Role.ADMIN,
        verified=True,
        is_demo=True,
    )
    try:
        with Session(engine) as db:
            seed_demo(db)
            db.commit()
            if db.scalar(
                select(imports.c.id).where(imports.c.label == label, imports.c.is_demo)
            ):
                return
            content = StringIO()
            writer = csv.writer(content)
            writer.writerow(CSV_FIELDS)
            for index in range(108):
                day = monday - timedelta(weeks=107 - index)
                price = 35 + (index % 26) // 3 + (index * 13 % 11) / 2
                writer.writerow(
                    [
                        day,
                        day,
                        "Pabna",
                        "Sujanagar · sample",
                        "farmgate",
                        "A",
                        "kg",
                        "",
                        f"{price:.2f}",
                        f"{price + 4:.2f}",
                        "https://example.invalid/peyajflow/synthetic",
                        f"FIXTURE-{day}",
                    ]
                )
            batch = import_csv(
                ImportInput(label=label, synthetic=True, csv=content.getvalue()),
                actor,
                db,
            )
            if batch["status"] == "pending":
                review_batch(batch["id"], ReviewImport(decision="approved"), actor, db)
            print(f"Synthetic batch: {batch['accepted_rows']} new rows")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
