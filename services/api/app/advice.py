from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import Actor, Input, Profile, Role, require_role
from app.database import DB
from app.forecast import Horizon, market_forecast
from app.lots import BDT, PositiveKg, get_lot, today
from app.market_data import FRESH_DAYS, approved, prices
from app.risk import lot_risk
from app.trade import ACTIVE_OFFERS, offer_expired, scoped_offer

router = APIRouter(prefix="/v1/lots/{lot_id}", tags=["Hold or sell"])
Amount = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]
Series = Annotated[str, Field(pattern="^[0-9a-f]{64}$")]


class AdviceInput(Input):
    series: Series | None = None
    horizon_days: Horizon = 7
    quantity_kg: PositiveKg | None = None
    offer_id: UUID | None = None
    manual_price_bdt_kg: BDT | None = None
    hypothetical_low: BDT | None = None
    hypothetical_middle: BDT | None = None
    hypothetical_high: BDT | None = None
    loss_pct: Annotated[Decimal, Field(ge=0, le=100, decimal_places=2)] = Decimal(0)
    transport_now_bdt: Amount = Decimal(0)
    fees_now_bdt: Amount = Decimal(0)
    storage_bdt: Amount = Decimal(0)
    finance_bdt: Amount = Decimal(0)
    transport_later_bdt: Amount = Decimal(0)
    fees_later_bdt: Amount = Decimal(0)
    cash_need_bdt: Amount = Decimal(0)
    assumptions_reviewed: bool = False

    @model_validator(mode="after")
    def coherent(self):
        future = (
            self.hypothetical_low,
            self.hypothetical_middle,
            self.hypothetical_high,
        )
        if any(point is not None for point in future) and (
            None in future or not future[0] <= future[1] <= future[2]
        ):
            raise ValueError("Supply all three hypothetical prices in ascending order")
        if self.offer_id and self.manual_price_bdt_kg is not None:
            raise ValueError("Use either an offer or a manual current price")
        return self


class AdviceView(BaseModel):
    recommendation: Literal["SELL", "HOLD", "SELL_PART", "INSUFFICIENT_DATA"]
    confidence: Literal["insufficient", "limited", "moderate"]
    reasons: list[str]
    risk_band: str
    horizon_days: Horizon
    quantity_kg: Decimal
    sale_now_price: Decimal | None = None
    sale_now_source: str | None = None
    future_source: str | None = None
    retained_kg: Decimal | None = None
    sell_now_net_bdt: Decimal | None = None
    hold_low_bdt: Decimal | None = None
    hold_middle_bdt: Decimal | None = None
    hold_high_bdt: Decimal | None = None
    loss_pct: Decimal
    now_cost_bdt: Decimal
    later_cost_bdt: Decimal
    synthetic: bool


def bdt(value: Decimal) -> Decimal:
    return value.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)


def evaluate(
    db: Session,
    actor: Profile,
    lot_id: UUID,
    body: AdviceInput,
) -> AdviceView:
    lot = get_lot(db, actor, lot_id)
    risk = lot_risk(lot_id, actor, db)
    sellable = (
        lot["verified_kg"] if lot["verified_kg"] is not None else lot["available_kg"]
    ) - lot["reserved_kg"]
    quantity = body.quantity_kg if body.quantity_kg is not None else sellable
    if quantity > sellable:
        raise HTTPException(409, "insufficient_stock")

    now_price = body.manual_price_bdt_kg
    now_source = "user_assumption" if now_price is not None else None
    future_source = None
    future = None
    synthetic = False
    verified_offer = False
    series_row = None
    if body.series:
        series_row = (
            db.execute(
                select(prices)
                .where(
                    approved(actor),
                    prices.c.series == body.series,
                )
                .order_by(prices.c.observed_on.desc(), prices.c.id)
                .limit(1)
            )
            .mappings()
            .one_or_none()
        )
        if series_row is None:
            raise HTTPException(404, "not_found")
        if (
            series_row["price_type"] != "farmgate"
            or series_row["district"].casefold() != lot["district"].casefold()
            or series_row["grade"] != lot["grade"]
        ):
            raise HTTPException(422, "advice_market_mismatch")
        synthetic = series_row["synthetic"]
        if (
            now_price is None
            and (today() - series_row["observed_on"]).days <= FRESH_DAYS
        ):
            now_price = (series_row["low_bdt_kg"] + series_row["high_bdt_kg"]) / 2
            now_source = "farmgate_reference"
        forecast = market_forecast(db, actor, body.series, body.horizon_days)
        if forecast.middle_bdt_kg is not None:
            future = (forecast.low_bdt_kg, forecast.middle_bdt_kg, forecast.high_bdt_kg)
            future_source = forecast.method
    if body.hypothetical_middle is not None:
        future = (
            body.hypothetical_low,
            body.hypothetical_middle,
            body.hypothetical_high,
        )
        future_source = "user_scenario"
    if body.offer_id:
        require_role(actor, Role.FARMER)
        offer = scoped_offer(db, actor, body.offer_id)
        if (
            offer["lot_id"] != lot_id
            or offer["status"] not in ACTIVE_OFFERS
            or offer_expired(offer)
            or offer["proposer_id"] != offer["buyer_membership_id"]
            or (offer["grade"], offer["variety"]) != (lot["grade"], lot["variety"])
        ):
            raise HTTPException(409, "invalid_transition")
        quantity = min(quantity, offer["quantity_kg"])
        now_price = offer["price_bdt_kg"]
        verified_offer = offer["buyer_verified"]
        now_source = (
            "verified_buyer_offer" if verified_offer else "unverified_buyer_offer"
        )

    now_cost = body.transport_now_bdt + body.fees_now_bdt
    later_cost = (
        body.storage_bdt
        + body.finance_bdt
        + body.transport_later_bdt
        + body.fees_later_bdt
    )
    retained = quantity * (1 - body.loss_pct / 100)
    immediate = (
        bdt(quantity * now_price - now_cost)
        if now_price is not None and quantity
        else None
    )
    holds = (
        [bdt(retained * value - later_cost) for value in future]
        if future and quantity
        else [None] * 3
    )
    reasons = []
    if quantity <= 0:
        reasons.append("no_sellable_quantity")
    if immediate is None:
        reasons.append("missing_current_price")
    if not future:
        reasons.append("missing_future_range")
    if synthetic:
        reasons.append("synthetic_series")
    if (
        now_source in {"user_assumption", "unverified_buyer_offer"}
        or future_source == "user_scenario"
    ):
        reasons.append("hypothetical_inputs")
    if risk.band != "low":
        reasons.append("review_storage_condition")
    if not body.assumptions_reviewed:
        reasons.append("review_costs_and_losses")

    recommendation, confidence = "INSUFFICIENT_DATA", "insufficient"
    if not reasons and immediate is not None and holds[0] is not None:
        margin = max(Decimal(1), abs(immediate) * Decimal(".05"))
        if (
            body.cash_need_bdt > 0
            and immediate >= body.cash_need_bdt
            and holds[1] > immediate + margin
            and quantity < sellable
        ):
            recommendation = "SELL_PART"
            reasons.append("liquidity_with_remaining_stock")
        elif immediate >= 0 and immediate > holds[2] + margin:
            recommendation = "SELL_PART" if quantity < sellable else "SELL"
            reasons.append("current_net_beats_upside")
        elif (
            body.cash_need_bdt == 0 and holds[0] >= 0 and holds[0] > immediate + margin
        ):
            recommendation = "HOLD"
            reasons.append("downside_beats_current_net")
        else:
            reasons.append("scenario_overlap_or_cash_need")
        if recommendation != "INSUFFICIENT_DATA":
            confidence = "moderate" if verified_offer else "limited"
    return AdviceView(
        recommendation=recommendation,
        confidence=confidence,
        reasons=reasons,
        risk_band=risk.band,
        horizon_days=body.horizon_days,
        quantity_kg=quantity,
        sale_now_price=bdt(now_price) if now_price is not None else None,
        sale_now_source=now_source,
        future_source=future_source,
        retained_kg=retained.quantize(Decimal(".001")),
        sell_now_net_bdt=immediate,
        hold_low_bdt=holds[0],
        hold_middle_bdt=holds[1],
        hold_high_bdt=holds[2],
        loss_pct=body.loss_pct,
        now_cost_bdt=now_cost,
        later_cost_bdt=later_cost,
        synthetic=synthetic,
    )


@router.get("/recommendation", response_model=AdviceView)
def default_advice(lot_id: UUID, actor: Actor, db: DB):
    return evaluate(db, actor, lot_id, AdviceInput())


@router.post("/recommendation", response_model=AdviceView)
def compare_advice(lot_id: UUID, body: AdviceInput, actor: Actor, db: DB):
    return evaluate(db, actor, lot_id, body)
