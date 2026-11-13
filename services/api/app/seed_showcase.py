"""Populate the isolated account workspace through the same services used by the UI."""

from datetime import timedelta
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid5

from fastapi import HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.datastructures import Headers, UploadFile

from app import demand, inspection, logistics, lots, settlement, trade, voice
from app.auth import (
    DEMO_MEMBERS,
    Profile,
    demo_enabled,
    demo_id,
    seed_demo,
    showcase_access_key,
)
from app.database import database_engine
from app.seed_market import main as seed_market

NAMESPACE = UUID("5bd94adc-530c-4664-b3be-a1207d8bfc49")


def key(name):
    return uuid5(NAMESPACE, name)


def profile(name):
    label, district, role, verified = DEMO_MEMBERS[name]
    return Profile(
        user_id=demo_id("user", name),
        membership_id=demo_id("membership", name),
        organization_id=demo_id("organization", name),
        organization=label,
        name=label,
        district=district,
        role=role,
        verified=verified,
        language="bn",
        is_demo=True,
    )


def seed(db):
    today = lots.today()
    farmer, salma, buyer, buyer_two, agent, operator = map(
        profile, ("farmer", "farmer-two", "buyer", "buyer-two", "agent", "admin")
    )
    seed_demo(db)
    db.commit()
    stock = {}
    for owner, label, grade, quantity, verified in (
        (farmer, "Sujanagar North Shed", "A", 1200, 1160),
        (farmer, "Ataikula Curing Bay", "B", 840, 820),
        (farmer, "Nawabganj West Store", "A", 600, None),
        (salma, "Pabna Riverbank Store", "A", 950, 910),
    ):
        request_key = key(label)
        current = db.execute(
            select(lots.lots.c.id).where(
                lots.lots.c.owner_membership_id == owner.membership_id,
                lots.lots.c.create_key == request_key,
            )
        ).scalar_one_or_none()
        if current is None:
            lot = lots.register_lot(
                lots.LotCreate(
                    label=label,
                    district="Pabna",
                    variety="Taherpuri",
                    storage_type="Ventilated bamboo shed",
                    harvest_on=today - timedelta(days=27),
                    stored_on=today - timedelta(days=20),
                    grade=grade,
                    listed=True,
                    quantity=quantity,
                    request_key=request_key,
                ),
                owner,
                db,
            )
            db.commit()
            current = lot.id
            if verified:
                lots.verify_lot(
                    current,
                    lots.Verification(verified_kg=verified),
                    agent if owner == farmer else operator,
                    db,
                )
        stock[label] = current

    if not db.scalar(
        select(demand.buyer_requests.c.id).where(
            demand.buyer_requests.c.buyer_membership_id == buyer.membership_id
        )
    ):
        demand.create_demand(
            demand.DemandInput(
                quantity_kg=500,
                variety="Taherpuri",
                minimum_grade="B",
                delivery_district="Dhaka",
                delivery_from=today,
                delivery_to=today + timedelta(days=7),
                price_ceiling_bdt_kg=53,
                transport="buyer",
            ),
            buyer,
            db,
        )

    for suffix, label, sender, receiver, qty, price, end in (
        ("pending", "Sujanagar North Shed", buyer, farmer, 320, 48.5, "sent"),
        ("booked", "Sujanagar North Shed", buyer, farmer, 240, 49, "booked"),
        ("delivered", "Ataikula Curing Bay", buyer, farmer, 180, 46, "verified"),
        ("counter", "Pabna Riverbank Store", buyer_two, salma, 210, 45, "countered"),
    ):
        offer_key = key(f"offer-{suffix}")
        if db.scalar(
            select(trade.offers.c.id).where(
                trade.offers.c.buyer_membership_id == sender.membership_id,
                trade.offers.c.create_key == offer_key,
            )
        ):
            continue
        offer = trade.create_offer(
            trade.OfferInput(
                lot_id=stock[label],
                quantity_kg=qty,
                price_bdt_kg=price,
                delivery_district="Dhaka",
                transport="buyer",
                valid_hours=168,
                request_key=offer_key,
            ),
            sender,
            db,
        )
        if end == "sent":
            continue
        if end == "countered":
            trade.respond(
                offer.id,
                trade.OfferReply(
                    action="counter",
                    version=offer.version,
                    request_key=key("counter"),
                    quantity_kg=200,
                    price_bdt_kg=47,
                ),
                receiver,
                db,
            )
            continue
        receipt = trade.respond(
            offer.id,
            trade.OfferReply(
                action="accept",
                version=offer.version,
                request_key=key(f"accept-{suffix}"),
                confirm=True,
            ),
            receiver,
            db,
        )
        order = receipt.order_id
        if end == "booked":
            request = logistics.create_request(
                logistics.RequestInput(
                    order_id=order,
                    pickup_on=today,
                    handling="Ventilated sacks with separate grade labels",
                    request_key=key("freight-request"),
                ),
                sender,
                db,
            )
            for provider, cost in (
                ("Padma Freight", 650),
                ("Dhaka Produce Transport", 760),
            ):
                quote = logistics.record_quote(
                    request.id,
                    logistics.QuoteInput(
                        provider=provider,
                        source_ref=f"PF-{cost}",
                        capacity_kg=400,
                        pickup_on=today,
                        freight_bdt=cost,
                        handling_bdt=80,
                        valid_hours=24,
                    ),
                    operator,
                    db,
                )
                if cost == 650:
                    booked_quote = quote.id
            logistics.book_quote(
                request.id,
                logistics.BookingInput(quote_id=booked_quote, confirm=True),
                sender,
                db,
            )
        else:
            for party, action in ((receiver, "dispatch"), (sender, "receive")):
                trade.transition(
                    order,
                    trade.OrderReply(
                        action=action, request_key=key(action), confirm=True
                    ),
                    party,
                    db,
                )
            report = settlement.report_payment(
                order,
                settlement.Report(
                    reference="PF-TRANSFER-0180",
                    request_key=key("payment"),
                    confirm=True,
                ),
                sender,
                db,
                Response(),
            )
            settlement.review_payment(
                order,
                report["id"],
                settlement.Review(
                    decision="verified",
                    evidence_reference="PF-RECEIPT-0180",
                    confirm=True,
                ),
                operator,
                db,
            )

    note = "Check ventilation and weigh the curing bay before the next collection."
    if not db.scalar(
        select(voice.tasks.c.id).where(
            voice.tasks.c.actor_id == farmer.membership_id, voice.tasks.c.note == note
        )
    ):
        voice.request_assistance(
            voice.AssistanceInput(
                kind="inspection",
                note=note,
                lot_id=stock["Ataikula Curing Bay"],
            ),
            farmer,
            db,
        )

    asset = Path(__file__).with_name("fixtures") / "onion-storage.webp"
    lot_id = stock["Sujanagar North Shed"]
    if asset.is_file() and not db.scalar(
        select(inspection.inspections.c.id).where(
            inspection.inspections.c.lot_id == lot_id
        )
    ):
        from PIL import Image

        with Image.open(asset) as image:
            details = image.crop(
                (80, image.height // 3, image.width * 2 // 3, image.height)
            )
            detail_file = BytesIO()
            details.save(detail_file, "WEBP", quality=82)
        detail_file.seek(0)
        headers = Headers({"content-type": "image/webp"})
        evidence = inspection.create_inspection(
            lot_id,
            farmer,
            db,
            inspection.Observations(
                observed_on=today,
                curing="cured",
                ventilation="good",
                moisture="dry",
                odor="normal",
                temperature_c=28,
                humidity_pct=66,
                sample_kg=12,
                visible_flags=["no_obvious_defect"],
                notes="Front row sampled from three ventilated sacks.",
            ).model_dump_json(),
            [
                UploadFile(
                    BytesIO(asset.read_bytes()), filename="shed.webp", headers=headers
                ),
                UploadFile(detail_file, filename="detail.webp", headers=headers),
            ],
            True,
        )
        inspection.review_inspection(
            lot_id,
            evidence.id,
            inspection.ReviewInput(
                flags=["no_obvious_defect"],
                reason="Dry outer skins and good airflow in the inspected row.",
            ),
            agent,
            db,
        )


def main():
    if not (demo_enabled() or showcase_access_key()):
        raise SystemExit(
            "Showcase accounts require the isolated development workspace."
        )
    engine = database_engine()
    if engine is None:
        raise SystemExit("Set DATABASE_URL before seeding.")
    try:
        with Session(engine) as db:
            seed(db)
        seed_market()
    except HTTPException as error:
        raise SystemExit(
            f"Showcase setup failed ({error.status_code}): {error.detail}"
        ) from error
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
