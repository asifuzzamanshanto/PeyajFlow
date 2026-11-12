from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Table,
    UniqueConstraint,
    Uuid,
    func,
    insert,
    select,
    text,
    update,
)
from sqlalchemy.orm import Session

from app.advice import Amount, bdt
from app.auth import Actor, Input, Profile, Role, ShortText, audit, require_role
from app.database import DB, metadata
from app.lots import PositiveKg, lots, payload_hash, today
from app.notifications import publish
from app.trade import now, offer_view, order_rows, participants

router = APIRouter(prefix="/v1", tags=["Logistics"])
DHAKA = ZoneInfo("Asia/Dhaka")

requests = Table(
    "logistics_requests",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid4),
    Column("order_id", ForeignKey("orders.id"), nullable=False, index=True),
    Column("requester_id", ForeignKey("memberships.id"), nullable=False),
    Column("request_key", Uuid, nullable=False),
    Column("request_hash", String(64), nullable=False),
    Column("status", String(12), nullable=False),
    Column("pickup_district", String(100), nullable=False),
    Column("delivery_district", String(100), nullable=False),
    Column("pickup_on", Date, nullable=False),
    Column("handling", String(100), nullable=False),
    Column("booked_quote_id", Uuid),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
    UniqueConstraint("order_id", "request_key", name="uq_logistics_request_key"),
)
Index(
    "uq_active_logistics_request",
    requests.c.order_id,
    unique=True,
    postgresql_where=text("status <> 'cancelled'"),
)

quotes = Table(
    "logistics_quotes",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid4),
    Column(
        "request_id", ForeignKey("logistics_requests.id"), nullable=False, index=True
    ),
    Column("operator_id", ForeignKey("memberships.id"), nullable=False),
    Column("provider", String(100), nullable=False),
    Column("source_ref", String(100), nullable=False),
    Column("capacity_kg", Numeric(12, 3), nullable=False),
    Column("pickup_on", Date, nullable=False),
    Column("freight_bdt", Numeric(12, 2), nullable=False),
    Column("handling_bdt", Numeric(12, 2), nullable=False),
    Column("valid_until", DateTime(timezone=True), nullable=False),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
    UniqueConstraint(
        "request_id", "provider", "source_ref", name="uq_logistics_quote_source"
    ),
    CheckConstraint(
        "capacity_kg > 0 and freight_bdt >= 0 and handling_bdt >= 0",
        name="valid_quote_amounts",
    ),
)


class RequestInput(Input):
    order_id: UUID
    pickup_on: date
    handling: ShortText
    request_key: UUID


class QuoteInput(Input):
    provider: ShortText
    source_ref: ShortText
    capacity_kg: PositiveKg
    pickup_on: date
    freight_bdt: Amount
    handling_bdt: Amount = Decimal(0)
    valid_hours: Annotated[int, Field(ge=1, le=168)] = 24


class BookingInput(Input):
    quote_id: UUID
    confirm: Literal[True]


class QuoteView(BaseModel):
    id: UUID
    provider: str
    source_ref: str
    capacity_kg: Decimal
    pickup_on: date
    freight_bdt: Decimal
    handling_bdt: Decimal
    valid_until: datetime
    expired: bool
    freight_total_bdt: Decimal
    buyer_landed_bdt: Decimal
    buyer_landed_bdt_kg: Decimal
    seller_net_before_other_costs_bdt: Decimal


class RequestView(BaseModel):
    id: UUID
    status: str
    pickup_district: str
    delivery_district: str
    pickup_on: date
    handling: str
    booked_quote_id: UUID | None
    created_at: datetime
    quotes: list[QuoteView]


class LogisticsView(BaseModel):
    order_id: UUID
    order_status: str
    responsible: Literal["buyer", "seller"]
    can_request: bool
    quantity_kg: Decimal
    goods_total_bdt: Decimal
    requests: list[RequestView]


def responsible(actor: Profile, offer) -> bool:
    membership = (
        "buyer_membership_id"
        if offer["transport"] == "buyer"
        else "seller_membership_id"
    )
    return actor.membership_id == offer[membership]


def confirmed(order):
    return order["status"] == "confirmed" and order["expires_at"] > now()


def require_responsible(actor: Profile, offer):
    if not responsible(actor, offer):
        raise HTTPException(403, "transport_responsibility_required")


def logistics_request(db: Session, request_id: UUID, actor: Profile):
    request = (
        db.execute(select(requests).where(requests.c.id == request_id))
        .mappings()
        .one_or_none()
    )
    if request is None:
        raise HTTPException(404, "not_found")
    order, offer = order_rows(db, actor, request["order_id"], lock=True)
    current = (
        db.execute(
            select(requests).where(requests.c.id == request_id).with_for_update()
        )
        .mappings()
        .one()
    )
    return current, order, offer


def eligible_pickup(
    pickup_on: date, order, offer, earliest: date | None = None
) -> None:
    # The existing reservation expires at its recorded deadline.
    last_pickup = min(
        order["expires_at"].astimezone(DHAKA).date(), offer["delivery_to"] or date.max
    )
    if not max(today(), earliest or date.min) <= pickup_on <= last_pickup:
        raise HTTPException(422, "logistics_pickup_window")


def quote_view(row, offer) -> QuoteView:
    fee = row["freight_bdt"] + row["handling_bdt"]
    goods = offer_view(offer).total_bdt
    buyer_landed = goods + fee if offer["transport"] == "buyer" else goods
    seller_net = goods - fee if offer["transport"] == "seller" else goods
    return QuoteView.model_validate(
        {
            **row,
            "expired": row["valid_until"] <= now() or row["pickup_on"] < today(),
            "freight_total_bdt": fee,
            "buyer_landed_bdt": buyer_landed,
            "buyer_landed_bdt_kg": bdt(buyer_landed / offer["quantity_kg"]),
            "seller_net_before_other_costs_bdt": seller_net,
        }
    )


@router.get("/orders/{order_id}/logistics", response_model=LogisticsView)
def order_logistics(order_id: UUID, actor: Actor, db: DB):
    order, offer = order_rows(db, actor, order_id)
    rows = (
        db.execute(
            select(requests)
            .where(requests.c.order_id == order_id)
            .order_by(requests.c.created_at.desc(), requests.c.id)
        )
        .mappings()
        .all()
    )
    all_quotes = db.execute(
        select(quotes)
        .where(quotes.c.request_id.in_([row["id"] for row in rows]))
        .order_by((quotes.c.freight_bdt + quotes.c.handling_bdt), quotes.c.id)
    ).mappings()
    by_request: dict[UUID, list[QuoteView]] = {}
    for quote in all_quotes:
        by_request.setdefault(quote["request_id"], []).append(quote_view(quote, offer))
    return LogisticsView(
        order_id=order_id,
        order_status=order["status"],
        responsible=offer["transport"],
        can_request=confirmed(order)
        and responsible(actor, offer)
        and all(row["status"] == "cancelled" for row in rows),
        quantity_kg=offer["quantity_kg"],
        goods_total_bdt=offer_view(offer).total_bdt,
        requests=[
            RequestView.model_validate({**row, "quotes": by_request.get(row["id"], [])})
            for row in rows
        ],
    )


class RequestReceipt(BaseModel):
    id: UUID
    status: str


def request_transport(
    body: RequestInput, actor: Profile, db: Session
) -> RequestReceipt:
    order, offer = order_rows(db, actor, body.order_id, lock=True)
    require_responsible(actor, offer)
    digest = payload_hash(body)
    previous = (
        db.execute(
            select(requests).where(
                requests.c.order_id == body.order_id,
                requests.c.request_key == body.request_key,
            )
        )
        .mappings()
        .one_or_none()
    )
    if previous is not None:
        if (
            previous["request_hash"] != digest
            or previous["requester_id"] != actor.membership_id
        ):
            raise HTTPException(409, "idempotency_conflict")
        return RequestReceipt.model_validate(previous)
    if not confirmed(order) or db.scalar(
        select(requests.c.id).where(
            requests.c.order_id == body.order_id,
            requests.c.status != "cancelled",
        )
    ):
        raise HTTPException(409, "invalid_transition")
    eligible_pickup(body.pickup_on, order, offer)
    pickup = db.scalar(select(lots.c.district).where(lots.c.id == offer["lot_id"]))
    row = (
        db.execute(
            insert(requests)
            .values(
                order_id=body.order_id,
                request_key=body.request_key,
                request_hash=digest,
                requester_id=actor.membership_id,
                status="requested",
                pickup_district=pickup,
                delivery_district=offer["delivery_district"],
                pickup_on=body.pickup_on,
                handling=body.handling,
            )
            .returning(requests)
        )
        .mappings()
        .one()
    )
    audit(db, actor, "logistics.requested", row["id"], order_id=str(body.order_id))
    publish(
        db,
        participants(offer) - {actor.membership_id},
        "logistics.requested",
        "logistics",
        body.order_id,
        str(row["id"]),
    )
    return RequestReceipt.model_validate(row)


@router.post(
    "/logistics/quote-requests", response_model=RequestReceipt, status_code=201
)
def create_request(body: RequestInput, actor: Actor, db: DB):
    result = request_transport(body, actor, db)
    db.commit()
    return result


@router.post(
    "/logistics/quote-requests/{request_id}/quotes",
    response_model=QuoteView,
    status_code=201,
)
def record_quote(request_id: UUID, body: QuoteInput, actor: Actor, db: DB):
    require_role(actor, Role.ADMIN)
    request, order, offer = logistics_request(db, request_id, actor)
    existing = (
        db.execute(
            select(quotes).where(
                quotes.c.request_id == request_id,
                quotes.c.provider == body.provider,
                quotes.c.source_ref == body.source_ref,
            )
        )
        .mappings()
        .one_or_none()
    )
    if existing is not None:
        raise HTTPException(409, "idempotency_conflict")
    if request["status"] not in {"requested", "quoted"} or not confirmed(order):
        raise HTTPException(409, "invalid_transition")
    if body.capacity_kg < offer["quantity_kg"]:
        raise HTTPException(422, "logistics_insufficient_capacity")
    eligible_pickup(body.pickup_on, order, offer, request["pickup_on"])
    row = (
        db.execute(
            insert(quotes)
            .values(
                **body.model_dump(exclude={"valid_hours"}),
                request_id=request_id,
                operator_id=actor.membership_id,
                valid_until=min(
                    order["expires_at"], now() + timedelta(hours=body.valid_hours)
                ),
            )
            .returning(quotes)
        )
        .mappings()
        .one()
    )
    db.execute(
        update(requests).where(requests.c.id == request_id).values(status="quoted")
    )
    audit(db, actor, "logistics.quote_recorded", row["id"], request_id=str(request_id))
    publish(
        db,
        participants(offer),
        "logistics.quote_recorded",
        "logistics",
        order["id"],
        str(row["id"]),
    )
    db.commit()
    return quote_view(row, offer)


@router.post(
    "/logistics/quote-requests/{request_id}/book", response_model=RequestReceipt
)
def book_quote(request_id: UUID, body: BookingInput, actor: Actor, db: DB):
    request, order, offer = logistics_request(db, request_id, actor)
    require_responsible(actor, offer)
    if request["status"] == "booked" and request["booked_quote_id"] == body.quote_id:
        return RequestReceipt.model_validate(request)
    if request["status"] != "quoted" or not confirmed(order):
        raise HTTPException(409, "invalid_transition")
    quote = (
        db.execute(
            select(quotes).where(
                quotes.c.id == body.quote_id, quotes.c.request_id == request_id
            )
        )
        .mappings()
        .one_or_none()
    )
    if quote is None:
        raise HTTPException(404, "not_found")
    if quote_view(quote, offer).expired:
        raise HTTPException(409, "logistics_quote_expired")
    row = (
        db.execute(
            update(requests)
            .where(requests.c.id == request_id)
            .values(
                status="booked",
                booked_quote_id=body.quote_id,
            )
            .returning(requests)
        )
        .mappings()
        .one()
    )
    audit(db, actor, "logistics.booked", request_id, quote_id=str(body.quote_id))
    publish(
        db,
        participants(offer),
        "logistics.booked",
        "logistics",
        order["id"],
        str(request_id),
    )
    db.commit()
    return RequestReceipt.model_validate(row)


@router.post(
    "/logistics/quote-requests/{request_id}/cancel", response_model=RequestReceipt
)
def cancel_request(request_id: UUID, actor: Actor, db: DB):
    request, order, offer = logistics_request(db, request_id, actor)
    require_responsible(actor, offer)
    if request["status"] == "cancelled":
        return RequestReceipt.model_validate(request)
    if request["status"] not in {"requested", "quoted", "booked"} or order[
        "status"
    ] not in {"confirmed", "expired", "cancelled"}:
        raise HTTPException(409, "invalid_transition")
    row = (
        db.execute(
            update(requests)
            .where(requests.c.id == request_id)
            .values(
                status="cancelled",
            )
            .returning(requests)
        )
        .mappings()
        .one()
    )
    audit(db, actor, "logistics.cancelled", request_id)
    publish(
        db,
        participants(offer),
        "logistics.cancelled",
        "logistics",
        order["id"],
        str(request_id),
    )
    db.commit()
    return RequestReceipt.model_validate(row)
