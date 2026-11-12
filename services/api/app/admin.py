from datetime import date, datetime, timedelta
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    Uuid,
    func,
    insert,
    select,
    update,
)

from app import trade, twilio
from app.auth import (
    Actor,
    Input,
    Role,
    audit,
    audit_log,
    memberships,
    organizations,
    require_role,
    users,
)
from app.database import DB, metadata
from app.lots import lots, today
from app.market_data import FRESH_DAYS, approved, imports, prices
from app.notifications import deliveries, notifications, publish

router = APIRouter(prefix="/v1/admin", tags=["Operations"])

resolutions = Table(
    "dispute_resolutions",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid4),
    Column("order_id", ForeignKey("orders.id"), nullable=False, index=True),
    Column("dispute_id", ForeignKey("trade_actions.id"), unique=True, nullable=False),
    Column("operator_id", ForeignKey("memberships.id"), nullable=False),
    Column("restored_status", String(12), nullable=False),
    Column("note", String(300), nullable=False),
    Column(
        "resolved_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    ),
)


class Overview(BaseModel):
    unverified_accounts: int
    unverified_lots: int
    pending_imports: int
    open_disputes: int
    pending_sms: int
    attention_sms: int
    carrier_events_24h: int | None


class Verification(BaseModel):
    membership_id: UUID
    name: str
    district: str
    role: Role
    verified: bool


class VerificationInput(Input):
    verified: bool


class DataQuality(BaseModel):
    series: str
    market: str
    district: str
    price_type: str
    grade: str
    synthetic: bool
    latest_on: date
    days: int
    status: Literal["stale", "short_history", "replay_available"]


class AuditEntry(BaseModel):
    id: UUID
    action: str
    actor_role: Role
    resource_id: UUID
    recorded_at: datetime


class AuditPage(BaseModel):
    items: list[AuditEntry]
    next_offset: int | None


class Dispute(BaseModel):
    id: UUID
    lot_label: str
    quantity_kg: str
    created_at: datetime


class ResolveInput(Input):
    note: Annotated[str, Field(min_length=5, max_length=300)]
    confirmed: Literal[True]


class Resolution(BaseModel):
    id: UUID
    order_id: UUID
    restored_status: Literal["dispatched", "delivered"]
    resolved_at: datetime


accounts = memberships.join(users).join(organizations)


def count(db, table, *filters):
    return db.scalar(select(func.count()).select_from(table).where(*filters))


@router.get("/overview", response_model=Overview)
def overview(actor: Actor, db: DB):
    require_role(actor, Role.ADMIN)
    demo = actor.is_demo
    sms = deliveries.join(notifications).join(memberships).join(organizations)
    return Overview(
        unverified_accounts=count(
            db,
            accounts,
            organizations.c.is_demo == demo,
            memberships.c.role != Role.ADMIN,
            users.c.verified.is_(False),
        ),
        unverified_lots=count(
            db, lots, lots.c.is_demo == demo, lots.c.verified_at.is_(None)
        ),
        pending_imports=count(
            db, imports, imports.c.is_demo == demo, imports.c.status == "pending"
        ),
        open_disputes=count(
            db,
            trade.orders.join(trade.offers),
            trade.offers.c.is_demo == demo,
            trade.orders.c.status == "disputed",
        ),
        pending_sms=count(
            db,
            sms,
            organizations.c.is_demo == demo,
            deliveries.c.status.in_(("queued", "sending")),
        ),
        attention_sms=count(
            db,
            sms,
            organizations.c.is_demo == demo,
            deliveries.c.status.in_(("unknown", "failed", "undelivered")),
        ),
        carrier_events_24h=None
        if demo
        else count(
            db,
            twilio.events,
            twilio.events.c.channel == "voice",
            twilio.events.c.received_at >= trade.now() - timedelta(days=1),
        ),
    )


@router.get("/verifications", response_model=list[Verification])
def verifications(
    actor: Actor,
    db: DB,
    pending_only: bool = True,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
):
    require_role(actor, Role.ADMIN)
    filters = [
        organizations.c.is_demo == actor.is_demo,
        memberships.c.role != Role.ADMIN,
    ]
    if pending_only:
        filters.append(users.c.verified.is_(False))
    return list(
        db.execute(
            select(
                memberships.c.id.label("membership_id"),
                memberships.c.role,
                users.c.name,
                users.c.district,
                users.c.verified,
            )
            .select_from(accounts)
            .where(*filters)
            .order_by(users.c.name, memberships.c.id)
            .offset(offset)
            .limit(50)
        ).mappings()
    )


@router.put("/verifications/{membership_id}", response_model=Verification)
def verify_account(membership_id: UUID, body: VerificationInput, actor: Actor, db: DB):
    require_role(actor, Role.ADMIN)
    row = (
        db.execute(
            select(
                memberships.c.id.label("membership_id"),
                memberships.c.role,
                users.c.id.label("user_id"),
                users.c.name,
                users.c.district,
                users.c.verified,
            )
            .select_from(accounts)
            .where(
                memberships.c.id == membership_id,
                organizations.c.is_demo == actor.is_demo,
                memberships.c.role != Role.ADMIN,
            )
            .with_for_update(of=users)
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise HTTPException(404, "not_found")
    if body.verified != row["verified"]:
        db.execute(
            update(users)
            .where(users.c.id == row["user_id"])
            .values(verified=body.verified)
        )
        audit(
            db,
            actor,
            "admin.account_verified" if body.verified else "admin.account_unverified",
            membership_id,
        )
        db.commit()
    return Verification.model_validate({**row, "verified": body.verified})


@router.get("/data-quality", response_model=list[DataQuality])
def quality(actor: Actor, db: DB):
    require_role(actor, Role.ADMIN)
    dimensions = (
        prices.c.series,
        prices.c.grade,
        prices.c.price_type,
        prices.c.synthetic,
    )
    rows = db.execute(
        select(
            *dimensions,
            func.min(prices.c.market).label("market"),
            func.min(prices.c.district).label("district"),
            func.max(prices.c.observed_on).label("latest_on"),
            func.count(func.distinct(prices.c.observed_on)).label("days"),
        )
        .where(approved(actor))
        .group_by(*dimensions)
        .order_by(func.max(prices.c.observed_on).desc(), prices.c.series)
        .limit(100)
    ).mappings()
    return [
        DataQuality.model_validate(
            {
                **row,
                "status": "stale"
                if (today() - row["latest_on"]).days > FRESH_DAYS
                else ("short_history" if row["days"] < 10 else "replay_available"),
            }
        )
        for row in rows
    ]


@router.get("/audit", response_model=AuditPage)
def search_audit(
    actor: Actor,
    db: DB,
    action: Annotated[
        str | None, Query(max_length=60, pattern=r"^[a-z0-9_.]+$")
    ] = None,
    resource_id: UUID | None = None,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
):
    require_role(actor, Role.ADMIN)
    filters = [organizations.c.is_demo == actor.is_demo]
    if action:
        filters.append(audit_log.c.action.startswith(action, autoescape=True))
    if resource_id:
        filters.append(audit_log.c.resource_id == resource_id)
    records = (
        db.execute(
            select(
                audit_log.c.id,
                audit_log.c.action,
                memberships.c.role.label("actor_role"),
                audit_log.c.resource_id,
                audit_log.c.recorded_at,
            )
            .select_from(audit_log.join(memberships).join(organizations))
            .where(*filters)
            .order_by(audit_log.c.recorded_at.desc(), audit_log.c.id.desc())
            .offset(offset)
            .limit(51)
        )
        .mappings()
        .all()
    )
    return AuditPage(
        items=[AuditEntry.model_validate(row) for row in records[:50]],
        next_offset=offset + 50 if len(records) > 50 else None,
    )


@router.get("/disputes", response_model=list[Dispute])
def disputes(actor: Actor, db: DB, offset: Annotated[int, Query(ge=0, le=10000)] = 0):
    require_role(actor, Role.ADMIN)
    rows = db.execute(
        select(
            trade.orders.c.id,
            trade.orders.c.created_at,
            trade.offers.c.lot_label,
            trade.offers.c.quantity_kg,
        )
        .select_from(trade.orders.join(trade.offers))
        .where(
            trade.orders.c.status == "disputed",
            trade.offers.c.is_demo == actor.is_demo,
        )
        .order_by(trade.orders.c.created_at.desc(), trade.orders.c.id)
        .offset(offset)
        .limit(50)
    ).mappings()
    return [
        Dispute.model_validate({**row, "quantity_kg": str(row["quantity_kg"])})
        for row in rows
    ]


@router.post("/disputes/{order_id}/resolve", response_model=Resolution)
def resolve_dispute(order_id: UUID, body: ResolveInput, actor: Actor, db: DB):
    require_role(actor, Role.ADMIN)
    order, offer = trade.order_rows(db, actor, order_id, lock=True)
    history = (trade.trade_actions.c.resource_id == order_id) & (
        trade.trade_actions.c.resource_type == "order"
    )
    dispute_id = db.scalar(
        select(trade.trade_actions.c.id)
        .where(history, trade.trade_actions.c.action == "disputed")
        .order_by(trade.trade_actions.c.recorded_at.desc(), trade.trade_actions.c.id)
        .limit(1)
    )
    if dispute_id is None:
        raise HTTPException(409, "invalid_transition")
    previous = (
        db.execute(select(resolutions).where(resolutions.c.dispute_id == dispute_id))
        .mappings()
        .one_or_none()
    )
    if previous is not None and previous["note"] == body.note:
        return previous
    if order["status"] != "disputed":
        raise HTTPException(409, "invalid_transition")
    state = db.scalar(
        select(trade.trade_actions.c.action)
        .where(history, trade.trade_actions.c.action.in_(("dispatched", "delivered")))
        .order_by(trade.trade_actions.c.recorded_at.desc(), trade.trade_actions.c.id)
        .limit(1)
    )
    if state is None:
        raise HTTPException(409, "dispute_requires_review")
    row = (
        db.execute(
            insert(resolutions)
            .values(
                order_id=order_id,
                dispute_id=dispute_id,
                operator_id=actor.membership_id,
                note=body.note,
                restored_status=state,
            )
            .returning(resolutions)
        )
        .mappings()
        .one()
    )
    db.execute(
        update(trade.orders).where(trade.orders.c.id == order_id).values(status=state)
    )
    trade.journal(
        db, "order", trade.Receipt(id=order_id, status=state), "dispute_resolved", actor
    )
    publish(
        db,
        trade.participants(offer),
        "order.dispute_resolved",
        "order",
        order_id,
        str(dispute_id),
    )
    db.commit()
    return row
