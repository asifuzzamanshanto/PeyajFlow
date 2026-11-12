from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from app.auth import Actor
from app.condition import VisibleFlag
from app.database import DB
from app.inspection import InspectionView, inspection_view, observations_query
from app.lots import get_lot, today

router = APIRouter(prefix="/v1/lots/{lot_id}", tags=["Storage risk"])
METHOD = "storage-checklist-v1"
REFERENCE = "https://postharvest.ucdavis.edu/produce-facts-sheets/onions-dry"
FRESH_DAYS = 7


class RiskView(BaseModel):
    band: Literal["high", "moderate", "low", "insufficient_data"]
    recommendation: Literal[
        "inspect_today", "inspect_soon", "monitor", "collect_evidence"
    ]
    reasons: list[str]
    missing: list[str]
    days_stored: int
    observed_on: date | None = None
    method: str = METHOD
    reference_url: str = REFERENCE


def assess(
    stored_on: date, current: date, inspection: InspectionView | None
) -> RiskView:
    days = (current - stored_on).days
    observed = inspection.observed_on if inspection else None
    if inspection is None or not stored_on <= inspection.observed_on <= current:
        return RiskView(
            band="insufficient_data",
            recommendation="collect_evidence",
            reasons=["no_current_inspection"],
            missing=["inspection"],
            days_stored=days,
            observed_on=observed,
        )
    if (current - inspection.observed_on).days > FRESH_DAYS:
        return RiskView(
            band="insufficient_data",
            recommendation="collect_evidence",
            reasons=["stale_inspection"],
            missing=["fresh_observations"],
            days_stored=days,
            observed_on=observed,
        )

    missing = [
        key
        for key in (
            "curing",
            "ventilation",
            "moisture",
            "odor",
            "temperature_c",
            "humidity_pct",
        )
        if getattr(inspection, key) in (None, "unknown")
    ]
    flags = inspection.effective_flags
    if VisibleFlag.UNCERTAIN in flags:
        missing.append("visible_condition")
    strong = [
        reason
        for reason, present in (
            ("visible_rot", VisibleFlag.ROT_OR_MOLD in flags),
            ("wet_storage", inspection.moisture == "wet"),
            ("off_odor", inspection.odor == "off"),
        )
        if present
    ]
    attention = [
        reason
        for reason, present in (
            ("sprouting", VisibleFlag.SPROUTING in flags),
            ("physical_damage", VisibleFlag.DAMAGE in flags),
            ("poor_ventilation", inspection.ventilation == "poor"),
            ("uncured_stock", inspection.curing == "uncured"),
            (
                "elevated_humidity",
                inspection.curing == "cured"
                and inspection.humidity_pct is not None
                and inspection.humidity_pct > 70,
            ),
            (
                "sprouting_temperature",
                days >= 14
                and inspection.temperature_c is not None
                and 5 <= inspection.temperature_c <= 25,
            ),
            (
                "warm_storage",
                inspection.temperature_c is not None and inspection.temperature_c > 25,
            ),
            (
                "freezing_conditions",
                inspection.temperature_c is not None and inspection.temperature_c < 0,
            ),
        )
        if present
    ]
    common = {"days_stored": days, "observed_on": observed, "missing": missing}
    if strong:
        return RiskView(
            band="high",
            recommendation="inspect_today",
            reasons=strong + attention,
            **common,
        )
    if attention:
        return RiskView(
            band="moderate", recommendation="inspect_soon", reasons=attention, **common
        )
    if missing:
        return RiskView(
            band="insufficient_data",
            recommendation="collect_evidence",
            reasons=["incomplete_inspection"],
            **common,
        )
    return RiskView(
        band="low", recommendation="monitor", reasons=["no_checklist_trigger"], **common
    )


@router.get("/risk", response_model=RiskView)
def lot_risk(lot_id: UUID, actor: Actor, db: DB):
    lot = get_lot(db, actor, lot_id)
    row = db.execute(observations_query(lot_id).limit(1)).mappings().one_or_none()
    inspection = inspection_view(db, row) if row is not None else None
    return assess(lot["stored_on"], today(), inspection)
