from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256
from typing import Annotated, Literal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Table,
    UniqueConstraint,
    Uuid,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from app.auth import (
    Actor,
    Input,
    Profile,
    Role,
    ShortText,
    audit,
    delegations,
    require_role,
)
from app.database import DB, metadata

router = APIRouter(prefix="/v1/lots", tags=["Stock"])
KG_STEP = Decimal("0.001")
MAX_KG = Decimal("999999999.999")
PositiveKg = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=3)]
NonnegativeKg = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=3)]
SignedKg = Annotated[Decimal, Field(max_digits=12, decimal_places=3)]
BDT = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]


class Grade(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    UNGRADED = "ungraded"


lots = Table(
    "lots",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid4),
    Column("owner_membership_id", ForeignKey("memberships.id"), nullable=False),
    Column("is_demo", Boolean, nullable=False),
    Column("label", String(100), nullable=False),
    Column("district", String(100), nullable=False),
    Column("variety", String(100), nullable=False),
    Column("storage_type", String(100), nullable=False),
    Column("harvest_on", Date, nullable=False),
    Column("stored_on", Date, nullable=False),
    Column("grade", String(10), nullable=False),
    Column("listed", Boolean, nullable=False),
    Column("initial_kg", Numeric(12, 3), nullable=False),
    Column("available_kg", Numeric(12, 3), nullable=False),
    Column("reserved_kg", Numeric(12, 3), nullable=False),
    Column("verified_kg", Numeric(12, 3)),
    Column("verified_at", DateTime(timezone=True)),
    Column("create_key", Uuid, nullable=False),
    Column("create_hash", String(64), nullable=False),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
    UniqueConstraint("owner_membership_id", "create_key", name="uq_lots_owner_create"),
    CheckConstraint(
        "initial_kg > 0 and available_kg >= reserved_kg and reserved_kg >= 0",
        name="lot_quantity_balanced",
    ),
    CheckConstraint(
        "verified_kg is null or (verified_kg >= reserved_kg and verified_kg <= available_kg)",
        name="lot_verified_within_stock",
    ),
    CheckConstraint("harvest_on <= stored_on", name="lot_date_order"),
)
lot_events = Table(
    "lot_events",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid4),
    Column("lot_id", ForeignKey("lots.id"), nullable=False, index=True),
    Column("actor_id", ForeignKey("memberships.id")),
    Column("event_type", String(32), nullable=False),
    Column("delta_kg", Numeric(12, 3), nullable=False),
    Column("reserved_delta_kg", Numeric(12, 3), nullable=False),
    Column("submitted_quantity", Numeric(12, 3)),
    Column("submitted_unit", String(8)),
    Column("kg_per_maund", Numeric(12, 3)),
    Column("reason", String(200), nullable=False),
    Column("related_order_id", Uuid),
    Column("request_key", Uuid, nullable=False),
    Column("request_hash", String(64), nullable=False),
    Column(
        "recorded_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    ),
    UniqueConstraint("lot_id", "request_key", name="uq_lot_events_request"),
)


def today() -> date:
    return datetime.now(ZoneInfo("Asia/Dhaka")).date()


class LotFields(Input):
    label: ShortText
    district: ShortText
    variety: ShortText
    storage_type: ShortText
    harvest_on: date
    stored_on: date
    grade: Grade
    listed: bool = False

    @model_validator(mode="after")
    def valid_dates(self):
        if not self.harvest_on <= self.stored_on <= today():
            raise ValueError("Dates must be ordered and cannot be in the future")
        return self


class LotCreate(LotFields):
    quantity: PositiveKg
    unit: Literal["kg", "maund"] = "kg"
    kg_per_maund: PositiveKg | None = None
    request_key: UUID


class Movement(Input):
    event_type: Literal["WEIGHED_ADJUSTMENT", "LOSS_REPORTED"]
    quantity: SignedKg
    unit: Literal["kg", "maund"] = "kg"
    kg_per_maund: PositiveKg | None = None
    reason: Annotated[str, Field(min_length=1, max_length=200)]
    request_key: UUID


class Verification(Input):
    verified_kg: NonnegativeKg


class LotEvent(BaseModel):
    id: UUID
    event_type: str
    delta_kg: Decimal
    reserved_delta_kg: Decimal
    submitted_quantity: Decimal | None
    submitted_unit: str | None
    kg_per_maund: Decimal | None
    reason: str
    recorded_at: datetime


class LotView(BaseModel):
    id: UUID
    label: str
    district: str
    variety: str
    storage_type: str
    harvest_on: date
    stored_on: date
    grade: Grade
    listed: bool
    initial_kg: Decimal
    available_kg: Decimal
    reserved_kg: Decimal
    sellable_kg: Decimal
    verified_kg: Decimal | None
    verified_at: datetime | None


class LotDetail(LotView):
    events: list[LotEvent]


def scoped_lots(actor: Profile):
    scope = lots.c.is_demo == actor.is_demo
    if actor.role == Role.FARMER:
        return scope & (lots.c.owner_membership_id == actor.membership_id)
    if actor.role == Role.AGENT:
        return scope & lots.c.owner_membership_id.in_(
            select(delegations.c.farmer_membership_id).where(
                delegations.c.agent_membership_id == actor.membership_id
            )
        )
    require_role(actor, Role.ADMIN)
    return scope


def get_lot(
    db: Session, actor: Profile, lot_id: UUID, *, lock: bool = False
) -> RowMapping:
    statement = select(lots).where(lots.c.id == lot_id, scoped_lots(actor))
    row = (
        db.execute(statement.with_for_update() if lock else statement)
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise HTTPException(404, "not_found")
    return row


def kilograms(quantity: Decimal, unit: str, conversion: Decimal | None) -> Decimal:
    if (unit == "maund") != (conversion is not None):
        raise HTTPException(422, "conversion_required")
    result = quantity * conversion if conversion is not None else quantity
    if abs(result) > MAX_KG or result.quantize(KG_STEP) != result:
        raise HTTPException(422, "invalid_quantity")
    return result.quantize(KG_STEP)


def payload_hash(body: Input) -> str:
    return sha256(body.model_dump_json(exclude={"request_key"}).encode()).hexdigest()


def record_event(
    db: Session,
    actor: Profile | None,
    lot_id: UUID,
    kind: str,
    reason: str,
    *,
    delta: Decimal = Decimal(0),
    reserved_delta: Decimal = Decimal(0),
    order_id: UUID | None = None,
    request_key: UUID | None = None,
    request_hash: str = "",
    submitted_quantity: Decimal | None = None,
    submitted_unit: str | None = None,
    kg_per_maund: Decimal | None = None,
) -> None:
    db.execute(
        insert(lot_events).values(
            lot_id=lot_id,
            actor_id=actor.membership_id if actor else None,
            event_type=kind,
            delta_kg=delta,
            reserved_delta_kg=reserved_delta,
            reason=reason,
            related_order_id=order_id,
            request_key=request_key or uuid4(),
            request_hash=request_hash,
            submitted_quantity=submitted_quantity,
            submitted_unit=submitted_unit,
            kg_per_maund=kg_per_maund,
        )
    )


def view(row: RowMapping) -> LotView:
    return LotView.model_validate(
        {
            **row,
            "sellable_kg": row["available_kg"] - row["reserved_kg"],
        }
    )


def detail(db: Session, row: RowMapping) -> LotDetail:
    events = db.execute(
        select(lot_events)
        .where(lot_events.c.lot_id == row["id"])
        .order_by(lot_events.c.recorded_at.desc(), lot_events.c.id)
        .limit(100)
    ).mappings()
    return LotDetail(
        **view(row).model_dump(),
        events=[LotEvent.model_validate(item) for item in events],
    )


@router.get("", response_model=list[LotView])
def list_lots(actor: Actor, db: DB, offset: Annotated[int, Query(ge=0)] = 0):
    rows = db.execute(
        select(lots)
        .where(scoped_lots(actor))
        .order_by(lots.c.created_at.desc(), lots.c.id)
        .offset(offset)
        .limit(50)
    ).mappings()
    return [view(row) for row in rows]


def register_lot(body: LotCreate, actor: Profile, db: Session):
    require_role(actor, Role.FARMER)
    kg = kilograms(body.quantity, body.unit, body.kg_per_maund)
    request_hash = payload_hash(body)
    fields = body.model_dump(
        exclude={"quantity", "unit", "kg_per_maund", "request_key"}
    )
    row = (
        db.execute(
            pg_insert(lots)
            .values(
                **fields,
                owner_membership_id=actor.membership_id,
                is_demo=actor.is_demo,
                create_key=body.request_key,
                create_hash=request_hash,
                initial_kg=kg,
                available_kg=kg,
                reserved_kg=0,
            )
            .on_conflict_do_nothing(constraint="uq_lots_owner_create")
            .returning(lots)
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        row = (
            db.execute(
                select(lots).where(
                    lots.c.owner_membership_id == actor.membership_id,
                    lots.c.create_key == body.request_key,
                )
            )
            .mappings()
            .one()
        )
        if row["create_hash"] != request_hash:
            raise HTTPException(409, "idempotency_conflict")
        return view(row)
    record_event(
        db,
        actor,
        row["id"],
        "HARVEST_ADDED",
        "lot_registered",
        delta=kg,
        submitted_quantity=body.quantity,
        submitted_unit=body.unit,
        kg_per_maund=body.kg_per_maund,
    )
    audit(db, actor, "lot.created", row["id"])
    return view(row)


@router.post("", response_model=LotView, status_code=201)
def create_lot(body: LotCreate, actor: Actor, db: DB):
    result = register_lot(body, actor, db)
    db.commit()
    return result


@router.get("/{lot_id}", response_model=LotDetail)
def read_lot(lot_id: UUID, actor: Actor, db: DB):
    return detail(db, get_lot(db, actor, lot_id))


@router.patch("/{lot_id}", response_model=LotView)
def edit_lot(lot_id: UUID, body: LotFields, actor: Actor, db: DB):
    require_role(actor, Role.FARMER)
    current = get_lot(db, actor, lot_id, lock=True)
    fields = body.model_dump()
    identity_changed = any(
        current[key] != fields[key] for key in ("variety", "grade", "harvest_on")
    )
    if identity_changed:
        if current["reserved_kg"]:
            raise HTTPException(409, "invalid_transition")
        fields.update(verified_kg=None, verified_at=None)
    row = (
        db.execute(
            update(lots).where(lots.c.id == lot_id).values(**fields).returning(lots)
        )
        .mappings()
        .one()
    )
    audit(db, actor, "lot.updated", lot_id)
    db.commit()
    return view(row)


def apply_movement(lot_id: UUID, body: Movement, actor: Profile, db: Session):
    require_role(actor, Role.FARMER, Role.AGENT)
    row = get_lot(db, actor, lot_id, lock=True)
    digest = payload_hash(body)
    previous = db.scalar(
        select(lot_events.c.request_hash).where(
            lot_events.c.lot_id == lot_id, lot_events.c.request_key == body.request_key
        )
    )
    if previous is not None:
        if previous != digest:
            raise HTTPException(409, "idempotency_conflict")
        return view(row)
    delta = kilograms(body.quantity, body.unit, body.kg_per_maund)
    if not delta or (body.event_type == "LOSS_REPORTED" and delta >= 0):
        raise HTTPException(422, "invalid_quantity")
    new_quantity = row["available_kg"] + delta
    if new_quantity < row["reserved_kg"]:
        raise HTTPException(409, "insufficient_stock")
    if new_quantity > MAX_KG:
        raise HTTPException(422, "invalid_quantity")
    verified = row["verified_kg"]
    if verified is not None and delta < 0:
        verified = max(row["reserved_kg"], verified + delta)
    updated = (
        db.execute(
            update(lots)
            .where(lots.c.id == lot_id)
            .values(
                available_kg=new_quantity,
                verified_kg=verified,
            )
            .returning(lots)
        )
        .mappings()
        .one()
    )
    record_event(
        db,
        actor,
        lot_id,
        body.event_type,
        body.reason,
        delta=delta,
        request_key=body.request_key,
        request_hash=digest,
        submitted_quantity=body.quantity,
        submitted_unit=body.unit,
        kg_per_maund=body.kg_per_maund,
    )
    audit(db, actor, "lot.movement", lot_id, kind=body.event_type)
    return view(updated)


@router.post("/{lot_id}/movements", response_model=LotView)
def move_lot(lot_id: UUID, body: Movement, actor: Actor, db: DB):
    result = apply_movement(lot_id, body, actor, db)
    db.commit()
    return result


@router.post("/{lot_id}/verification", response_model=LotView)
def verify_lot(lot_id: UUID, body: Verification, actor: Actor, db: DB):
    require_role(actor, Role.AGENT, Role.ADMIN)
    current = get_lot(db, actor, lot_id, lock=True)
    if not current["reserved_kg"] <= body.verified_kg <= current["available_kg"]:
        raise HTTPException(422, "invalid_quantity")
    row = (
        db.execute(
            update(lots)
            .where(lots.c.id == lot_id)
            .values(
                verified_kg=body.verified_kg,
                verified_at=func.now(),
            )
            .returning(lots)
        )
        .mappings()
        .one()
    )
    audit(db, actor, "lot.verified", lot_id, verified_kg=str(body.verified_kg))
    db.commit()
    return view(row)
