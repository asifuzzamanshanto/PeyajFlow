from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

from app.risk import assess

CURRENT = date(2026, 11, 12)


def observations(**changes):
    return SimpleNamespace(
        **{
            "observed_on": CURRENT,
            "curing": "cured",
            "ventilation": "good",
            "moisture": "dry",
            "odor": "normal",
            "temperature_c": Decimal("4"),
            "humidity_pct": Decimal("70"),
            "effective_flags": ["no_obvious_defect"],
            **changes,
        }
    )


def test_storage_risk_thresholds_and_freshness():
    stored = CURRENT - timedelta(days=14)
    assert assess(stored, CURRENT, observations()).band == "low"
    assert assess(
        stored, CURRENT, observations(temperature_c=Decimal("26"))
    ).reasons == ["warm_storage"]
    assert assess(
        stored, CURRENT, observations(temperature_c=Decimal("-1"))
    ).reasons == ["freezing_conditions"]
    assert assess(
        stored, CURRENT, observations(humidity_pct=Decimal("70.1"))
    ).reasons == ["elevated_humidity"]
    assert assess(
        stored, CURRENT, observations(temperature_c=Decimal("5"))
    ).reasons == ["sprouting_temperature"]
    assert (
        assess(
            stored + timedelta(days=1),
            CURRENT,
            observations(temperature_c=Decimal("5")),
        ).band
        == "low"
    )
    assert (
        assess(stored, CURRENT, observations(humidity_pct=None)).band
        == "insufficient_data"
    )
    assert (
        assess(stored, CURRENT, observations(humidity_pct=None, moisture="wet")).band
        == "high"
    )
    assert assess(
        stored,
        CURRENT,
        observations(observed_on=CURRENT - timedelta(days=8), moisture="wet"),
    ).reasons == ["stale_inspection"]
