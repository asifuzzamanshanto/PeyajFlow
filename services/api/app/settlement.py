from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
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

from app import trade
from app.auth import Actor, Input, Role, audit, require_role
from app.database import DB, metadata
from app.notifications import publish

router = APIRouter(prefix="/v1", tags=["Settlement evidence"])
PaymentStatus = Literal["reported", "verified", "rejected"]
Reference = Annotated[str, Field(min_length=3, max_length=100, pattern=r"^[^\r\n\t]+$")]

payments = Table(
    "order_payment_reports",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid4),
    Column("order_id", ForeignKey("orders.id"), nullable=False),
    Column("buyer_id", ForeignKey("memberships.id"), nullable=False),
    Column("request_key", Uuid, nullable=False),
    Column("reference", String(100), nullable=False),
    Column("status", String(10), nullable=False),
    Column(
        "reported_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    ),
    Column("reviewer_id", ForeignKey("memberships.id")),
    Column("review_reference", String(100)),
    Column("reviewed_at", DateTime(timezone=True)),
    UniqueConstraint("order_id", "request_key", name="uq_payment_report_key"),
    CheckConstraint(
        "(status = 'reported' and reviewer_id is null and review_reference is null and reviewed_at is null) "
        "or (status in ('verified', 'rejected') and reviewer_id is not null "
        "and review_reference is not null and reviewed_at is not null)",
        name="payment_report_review_state",
    ),
)
Index(
    "uq_active_payment_report",
    payments.c.order_id,
    unique=True,
    postgresql_where=text("status in ('reported', 'verified')"),
)
Index(
    "ix_pending_payment_reported_at",
    payments.c.reported_at,
    postgresql_where=text("status = 'reported'"),
)


class Report(Input):
    reference: Reference
    request_key: UUID
    confirm: Literal[True]


class Review(Input):
    decision: Literal["verified", "rejected"]
    evidence_reference: Reference
    confirm: Literal[True]


class Payment(BaseModel):
    id: UUID
    status: PaymentStatus
    reference: str
    reported_at: datetime
    reviewed_at: datetime | None


class Settlement(BaseModel):
    status: Literal["pending", "reported", "verified"]
    total_bdt: Decimal
    reports: list[Payment]


class QueueEntry(Payment):
    order_id: UUID
    lot_label: str
    total_bdt: Decimal


@router.get("/orders/{order_id}/settlement", response_model=Settlement)
def settlement(order_id: UUID, actor: Actor, db: DB):
    _, offer = trade.order_rows(db, actor, order_id)
    rows = (
        db.execute(
            select(payments)
            .where(payments.c.order_id == order_id)
            .order_by(payments.c.reported_at.desc(), payments.c.id)
            .limit(50)
        )
        .mappings()
        .all()
    )
    status = next(
        (row["status"] for row in rows if row["status"] != "rejected"), "pending"
    )
    return Settlement(
        status=status, total_bdt=trade.offer_view(offer).total_bdt, reports=rows
    )


@router.post("/orders/{order_id}/settlement", response_model=Payment, status_code=201)
def report_payment(
    order_id: UUID, body: Report, actor: Actor, db: DB, response: Response
):
    require_role(actor, Role.BUYER)
    order, offer = trade.order_rows(db, actor, order_id, lock=True)
    existing = (
        db.execute(
            select(payments).where(
                payments.c.order_id == order_id,
                payments.c.request_key == body.request_key,
            )
        )
        .mappings()
        .one_or_none()
    )
    if existing is not None:
        if existing["reference"] != body.reference:
            raise HTTPException(409, "idempotency_conflict")
        response.status_code = 200
        return existing
    if order["status"] != "delivered":
        raise HTTPException(409, "payment_requires_delivery")
    if db.scalar(
        select(payments.c.id).where(
            payments.c.order_id == order_id, payments.c.status != "rejected"
        )
    ):
        raise HTTPException(409, "payment_report_exists")
    row = (
        db.execute(
            insert(payments)
            .values(
                order_id=order_id,
                buyer_id=actor.membership_id,
                request_key=body.request_key,
                reference=body.reference,
                status="reported",
            )
            .returning(payments)
        )
        .mappings()
        .one()
    )
    audit(db, actor, "payment.reported", order_id)
    publish(
        db,
        {offer["seller_membership_id"]},
        "payment.reported",
        "order",
        order_id,
        str(row["id"]),
    )
    db.commit()
    return row


@router.get("/admin/settlements", response_model=list[QueueEntry])
def review_queue(
    actor: Actor, db: DB, offset: Annotated[int, Query(ge=0, le=10000)] = 0
):
    require_role(actor, Role.ADMIN)
    rows = db.execute(
        select(
            payments,
            trade.offers.c.lot_label,
            trade.offers.c.quantity_kg,
            trade.offers.c.price_bdt_kg,
        )
        .select_from(payments.join(trade.orders).join(trade.offers))
        .where(
            payments.c.status == "reported",
            trade.offers.c.is_demo == actor.is_demo,
            trade.orders.c.status == "delivered",
        )
        .order_by(payments.c.reported_at, payments.c.id)
        .offset(offset)
        .limit(50)
    ).mappings()
    return [
        {**row, "total_bdt": trade.order_total(row["quantity_kg"], row["price_bdt_kg"])}
        for row in rows
    ]


@router.post(
    "/orders/{order_id}/settlement/{payment_id}/review", response_model=Payment
)
def review_payment(
    order_id: UUID, payment_id: UUID, body: Review, actor: Actor, db: DB
):
    require_role(actor, Role.ADMIN)
    order, offer = trade.order_rows(db, actor, order_id, lock=True)
    row = (
        db.execute(
            select(payments).where(
                payments.c.order_id == order_id, payments.c.id == payment_id
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise HTTPException(404, "not_found")
    if row["status"] != "reported":
        if (
            row["status"] == body.decision
            and row["review_reference"] == body.evidence_reference
        ):
            return row
        raise HTTPException(409, "payment_already_reviewed")
    if order["status"] != "delivered":
        raise HTTPException(409, "payment_requires_delivery")
    if body.evidence_reference.casefold() == row["reference"].casefold():
        raise HTTPException(422, "payment_independent_evidence_required")
    row = (
        db.execute(
            update(payments)
            .where(payments.c.id == payment_id)
            .values(
                status=body.decision,
                reviewer_id=actor.membership_id,
                review_reference=body.evidence_reference,
                reviewed_at=func.now(),
            )
            .returning(payments)
        )
        .mappings()
        .one()
    )
    action = f"payment.{body.decision}"
    audit(db, actor, action, order_id)
    publish(db, trade.participants(offer), action, "order", order_id, str(payment_id))
    db.commit()
    return row
