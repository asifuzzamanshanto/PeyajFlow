from datetime import date
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, model_validator
from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Table,
    Uuid,
    case,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from app.auth import Actor, Input, Profile, Role, ShortText, audit, require_role
from app.database import DB, metadata
from app.lots import BDT, Grade, PositiveKg, lots, today

router = APIRouter(prefix="/v1", tags=["Buyer demand"])
PAGE_SIZE = 20

buyer_requests = Table(
    "buyer_requests",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid4),
    Column(
        "buyer_membership_id", ForeignKey("memberships.id"), nullable=False, index=True
    ),
    Column("quantity_kg", Numeric(12, 3), nullable=False),
    Column("variety", String(100), nullable=False),
    Column("minimum_grade", String(10), nullable=False),
    Column("delivery_district", String(100), nullable=False),
    Column("delivery_from", Date, nullable=False),
    Column("delivery_to", Date, nullable=False),
    Column("price_ceiling_bdt_kg", Numeric(10, 2)),
    Column("transport", String(12), nullable=False),
    Column("status", String(8), nullable=False),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
    CheckConstraint(
        "quantity_kg > 0 and delivery_from <= delivery_to", name="buyer_request_terms"
    ),
)


class DemandInput(Input):
    quantity_kg: PositiveKg
    variety: ShortText
    minimum_grade: Grade = Grade.UNGRADED
    delivery_district: ShortText
    delivery_from: date
    delivery_to: date
    price_ceiling_bdt_kg: BDT | None = None
    transport: Literal["buyer", "seller"]

    @model_validator(mode="after")
    def delivery_window(self):
        if not today() <= self.delivery_from <= self.delivery_to:
            raise ValueError("Delivery window must start today or later")
        return self


class DemandView(BaseModel):
    id: UUID
    quantity_kg: Decimal
    variety: str
    minimum_grade: Grade
    delivery_district: str
    delivery_from: date
    delivery_to: date
    price_ceiling_bdt_kg: Decimal | None
    transport: Literal["buyer", "seller"]
    status: Literal["open", "closed"]


class SupplyView(BaseModel):
    id: UUID
    district: str
    variety: str
    grade: Grade
    sellable_kg: Decimal
    verification: Literal["verified", "self_reported"]
    matched_kg: Decimal | None = None
    coverage: Literal["full", "partial"] | None = None
    preferred_pickup: bool | None = None
    estimated_landed_bdt: Decimal | None = None
    estimated_landed_bdt_kg: Decimal | None = None
    estimate_basis: Literal["buyer_assumptions"] | None = None


class SupplyPage(BaseModel):
    items: list[SupplyView]
    next_offset: int | None


class DemandPage(BaseModel):
    items: list[DemandView]
    next_offset: int | None


GRADE_RANK = {Grade.UNGRADED: 0, Grade.C: 1, Grade.B: 2, Grade.A: 3}
verified_stock = lots.c.verified_kg.is_not(None)
sale_stock = func.coalesce(lots.c.verified_kg, lots.c.available_kg) - lots.c.reserved_kg


def demand_for(
    db: Session, buyer: Profile, request_id: UUID, *, lock: bool = False
) -> RowMapping:
    stmt = select(buyer_requests).where(
        buyer_requests.c.id == request_id,
        buyer_requests.c.buyer_membership_id == buyer.membership_id,
    )
    row = db.execute(stmt.with_for_update() if lock else stmt).mappings().one_or_none()
    if row is None:
        raise HTTPException(404, "not_found")
    return row


def listed_lot_filter(actor: Profile):
    return (lots.c.is_demo == actor.is_demo) & lots.c.listed & (sale_stock > 0)


@router.get("/buyer-requests", response_model=DemandPage)
def list_demands(actor: Actor, db: DB, offset: Annotated[int, Query(ge=0)] = 0):
    require_role(actor, Role.BUYER)
    rows = (
        db.execute(
            select(buyer_requests)
            .where(buyer_requests.c.buyer_membership_id == actor.membership_id)
            .order_by(buyer_requests.c.created_at.desc(), buyer_requests.c.id)
            .offset(offset)
            .limit(PAGE_SIZE + 1)
        )
        .mappings()
        .all()
    )
    return DemandPage(
        items=[DemandView.model_validate(row) for row in rows[:PAGE_SIZE]],
        next_offset=offset + PAGE_SIZE if len(rows) > PAGE_SIZE else None,
    )


@router.post("/buyer-requests", response_model=DemandView, status_code=201)
def create_demand(body: DemandInput, actor: Actor, db: DB):
    require_role(actor, Role.BUYER)
    row = (
        db.execute(
            insert(buyer_requests)
            .values(
                **body.model_dump(),
                buyer_membership_id=actor.membership_id,
                status="open",
            )
            .returning(buyer_requests)
        )
        .mappings()
        .one()
    )
    audit(db, actor, "demand.created", row["id"])
    db.commit()
    return DemandView.model_validate(row)


@router.post("/buyer-requests/{request_id}/close", response_model=DemandView)
def close_demand(request_id: UUID, actor: Actor, db: DB):
    require_role(actor, Role.BUYER)
    current = demand_for(db, actor, request_id, lock=True)
    if current["status"] == "closed":
        return DemandView.model_validate(current)
    row = (
        db.execute(
            update(buyer_requests)
            .where(buyer_requests.c.id == request_id)
            .values(status="closed")
            .returning(buyer_requests)
        )
        .mappings()
        .one()
    )
    audit(db, actor, "demand.closed", request_id)
    db.commit()
    return DemandView.model_validate(row)


@router.get("/buyer-requests/{request_id}", response_model=DemandView)
def read_demand(request_id: UUID, actor: Actor, db: DB):
    require_role(actor, Role.BUYER)
    return DemandView.model_validate(demand_for(db, actor, request_id))


@router.get("/matches", response_model=SupplyPage, response_model_exclude_unset=True)
def browse_supply(
    actor: Actor,
    db: DB,
    district: Annotated[str | None, Query(max_length=100)] = None,
    variety: Annotated[str | None, Query(max_length=100)] = None,
    minimum_grade: Grade = Grade.UNGRADED,
    minimum_kg: PositiveKg | None = None,
    verified_only: bool = False,
    request_id: UUID | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    ranked: bool = False,
    preferred_district: Annotated[str | None, Query(max_length=100)] = None,
    price_assumption_bdt_kg: BDT | None = None,
    preferred_freight_bdt: Annotated[
        Decimal | None, Query(ge=0, max_digits=12, decimal_places=2)
    ] = None,
    other_freight_bdt: Annotated[
        Decimal | None, Query(ge=0, max_digits=12, decimal_places=2)
    ] = None,
):
    require_role(actor, Role.BUYER)
    demand = None
    if request_id is not None:
        demand = demand_for(db, actor, request_id)
        if demand["status"] != "open" or demand["delivery_to"] < today():
            raise HTTPException(409, "invalid_transition")
        variety = demand["variety"]
        minimum_grade = Grade(demand["minimum_grade"])
    filters = [listed_lot_filter(actor)]
    if district:
        filters.append(lots.c.district.icontains(district.strip(), autoescape=True))
    if variety:
        filters.append(func.lower(lots.c.variety) == variety.strip().lower())
    if minimum_grade != Grade.UNGRADED:
        filters.append(
            lots.c.grade.in_(
                [
                    grade
                    for grade, rank in GRADE_RANK.items()
                    if rank >= GRADE_RANK[minimum_grade]
                ]
            )
        )
    if minimum_kg is not None:
        filters.append(sale_stock >= minimum_kg)
    if verified_only:
        filters.append(verified_stock)
    extras = []
    ordering = [verified_stock.desc(), sale_stock.desc(), lots.c.id]
    if ranked and demand is not None:
        wanted = demand["quantity_kg"]
        matched = func.least(sale_stock, wanted)
        full = sale_stock >= wanted
        preferred = (
            func.lower(lots.c.district) == (preferred_district or "").strip().lower()
        )
        grade_rank = case(GRADE_RANK, value=lots.c.grade, else_=0)
        ordering = [
            full.desc(),
            preferred.desc(),
            verified_stock.desc(),
            grade_rank.desc(),
            matched.desc(),
            lots.c.id,
        ]
        extras = [
            matched.label("matched_kg"),
            case((full, "full"), else_="partial").label("coverage"),
            preferred.label("preferred_pickup"),
        ]
        if price_assumption_bdt_kg is not None and (
            preferred_freight_bdt is not None or other_freight_bdt is not None
        ):
            freight = case((preferred, preferred_freight_bdt), else_=other_freight_bdt)
            total = matched * price_assumption_bdt_kg + freight
            unit_cost = total / matched
            ordering.insert(1, unit_cost.asc().nulls_last())
            extras.extend(
                [
                    func.round(total, 2).label("estimated_landed_bdt"),
                    func.round(unit_cost, 2).label("estimated_landed_bdt_kg"),
                    case((total.is_not(None), "buyer_assumptions")).label(
                        "estimate_basis"
                    ),
                ]
            )
    rows = (
        db.execute(
            select(
                lots.c.id,
                lots.c.district,
                lots.c.variety,
                lots.c.grade,
                sale_stock.label("sellable_kg"),
                case((verified_stock, "verified"), else_="self_reported").label(
                    "verification"
                ),
                *extras,
            )
            .where(*filters)
            .order_by(*ordering)
            .offset(offset)
            .limit(PAGE_SIZE + 1)
        )
        .mappings()
        .all()
    )
    return SupplyPage(
        items=[SupplyView.model_validate(row) for row in rows[:PAGE_SIZE]],
        next_offset=offset + PAGE_SIZE if len(rows) > PAGE_SIZE else None,
    )
