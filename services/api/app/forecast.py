from bisect import bisect_left, bisect_right
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from functools import cache
from statistics import median
from typing import Annotated, Literal, cast

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import Actor, Profile
from app.database import DB
from app.lots import today
from app.market_data import FRESH_DAYS, approved, prices
from app.price_model import MODEL_METHOD, MarketPattern, market_pattern, predict_price

router = APIRouter(prefix="/v1/market", tags=["Forecasts"])
Horizon = Literal[7, 14, 28]
SeriesKey = Annotated[str, Query(pattern="^[0-9a-f]{64}$")]
BASELINES = ("last_value", "rolling_median", "seasonal_naive")
CANDIDATE = "historical_change_quantiles"
MIN_POINT = Decimal("0.01")


@dataclass(frozen=True)
class Report:
    observed: date
    published: date
    price: Decimal


@dataclass(frozen=True)
class Band:
    low: Decimal
    middle: Decimal
    high: Decimal


class Metrics(BaseModel):
    method: str
    observations: int
    mae_bdt_kg: Decimal
    wape_pct: Decimal | None
    interval_coverage_pct: Decimal
    pinball_bdt_kg: Decimal


class ModelPreview(BaseModel):
    method: Literal["lagged_price_neighbors"] = MODEL_METHOD
    low_bdt_kg: Decimal
    middle_bdt_kg: Decimal
    high_bdt_kg: Decimal


class ForecastView(BaseModel):
    status: Literal["baseline", "quantile", "insufficient_data", "stale"]
    method: str | None = None
    horizon_days: Horizon
    synthetic: bool
    as_of: date
    last_observed: date | None = None
    target_on: date
    history_count: int
    low_bdt_kg: Decimal | None = None
    middle_bdt_kg: Decimal | None = None
    high_bdt_kg: Decimal | None = None
    backtest: list[Metrics]
    model_preview: ModelPreview | None = None


def available(reports: list[Report], origin: date) -> dict[date, Decimal]:
    grouped: dict[date, list[Decimal]] = defaultdict(list)
    for entry in reports:
        if entry.observed <= origin and entry.published <= origin:
            grouped[entry.observed].append(entry.price)
    return {day: median(grouped[day]) for day in sorted(grouped)}


def quantile(values: list[Decimal], fraction: str) -> Decimal:
    sorted_values = sorted(values)
    index = Decimal(fraction) * (len(values) - 1)
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    return sorted_values[lower] + (index - lower) * (
        sorted_values[upper] - sorted_values[lower]
    )


def points(
    history: dict[date, Decimal], origin: date, horizon: int
) -> dict[str, Decimal]:
    days = list(history)
    if len(days) < 4 or (origin - days[-1]).days > FRESH_DAYS:
        return {}
    result = {
        "last_value": history[days[-1]],
        "rolling_median": median([history[key] for key in days[-4:]]),
    }
    seasonal_on = origin + timedelta(days=horizon - 364)
    left = bisect_left(days, seasonal_on - timedelta(days=3))
    right = bisect_right(days, seasonal_on + timedelta(days=3))
    if left < right:
        nearest = min(days[left:right], key=lambda key: (abs(key - seasonal_on), key))
        result["seasonal_naive"] = history[nearest]
    return result


def estimate(
    history: dict[date, Decimal],
    origin: date,
    horizon: int,
    calibration: dict[date, dict[str, Decimal]],
    model_point: Decimal | None,
) -> dict[str, Band]:
    if len(history) < 10:
        return {}
    delta = timedelta(days=horizon)
    residuals: dict[str, list[Decimal]] = defaultdict(list)
    for day in sorted(calibration):
        actual = history.get(day + delta)
        if actual is None:
            continue
        for method, prediction in calibration[day].items():
            residuals[method].append(actual - prediction)
    point_estimates = points(history, origin, horizon)
    if model_point is not None:
        point_estimates[MODEL_METHOD] = max(MIN_POINT, model_point)
    result = {}
    for method, point in point_estimates.items():
        errors = residuals[method][-60:]
        if len(errors) >= 6:
            result[method] = Band(
                max(MIN_POINT, min(point, point + quantile(errors, ".10"))),
                point,
                max(point, point + quantile(errors, ".90")),
            )
    changes = residuals["last_value"][-60:]
    if len(history) >= 70 and len(changes) >= 25 and "last_value" in point_estimates:
        current = point_estimates["last_value"]
        result[CANDIDATE] = Band(
            *(
                max(MIN_POINT, current + quantile(changes, q))
                for q in (".10", ".50", ".90")
            )
        )
    return result


def metrics(method: str, folds: list[tuple[Band, Decimal]]) -> Metrics:
    errors = sum(abs(actual - band.middle) for band, actual in folds)
    actual_total = sum(actual for _, actual in folds)
    inside = sum(band.low <= actual <= band.high for band, actual in folds)
    pinball = Decimal(0)
    for band, actual in folds:
        for point, q in (
            (band.low, Decimal(".1")),
            (band.middle, Decimal(".5")),
            (band.high, Decimal(".9")),
        ):
            error = actual - point
            pinball += max(q * error, (q - 1) * error)
    return Metrics(
        method=method,
        observations=len(folds),
        mae_bdt_kg=errors / len(folds),
        wape_pct=100 * errors / actual_total if actual_total else None,
        interval_coverage_pct=Decimal(100 * inside) / len(folds),
        pinball_bdt_kg=pinball / (len(folds) * 3),
    )


def passes_gate(candidate: Metrics, reference: list[Metrics]) -> bool:
    return (
        candidate.observations >= 24
        and bool(reference)
        and candidate.mae_bdt_kg
        < min(item.mae_bdt_kg for item in reference) * Decimal(".90")
        and 70 <= candidate.interval_coverage_pct <= 95
    )


def forecast_series(
    reports: list[Report], origin: date, horizon: Horizon, synthetic: bool
) -> ForecastView:
    history = available(reports, origin)
    latest = max(history, default=None)
    delta = timedelta(days=horizon)
    context = dict(
        horizon_days=horizon,
        synthetic=synthetic,
        as_of=origin,
        last_observed=latest,
        target_on=origin + delta,
        history_count=len(history),
    )
    if latest is None or (origin - latest).days > FRESH_DAYS:
        return ForecastView(
            status="stale" if latest else "insufficient_data", backtest=[], **context
        )
    snapshots = {}
    previous = None
    for day in reversed(history):
        if day + delta not in history or (
            previous is not None and (previous - day).days < 7
        ):
            continue
        snapshots[day] = available(reports, day)
        previous = day
    calibration = {
        day: points(snapshot, day, horizon) for day, snapshot in snapshots.items()
    }

    @cache
    def pattern_at(day: date) -> MarketPattern | None:
        snapshot = snapshots.get(day)
        if snapshot is None:
            snapshot = available(reports, day)
        return market_pattern(snapshot, day, horizon, FRESH_DAYS)

    for day, snapshot in snapshots.items():
        pattern = pattern_at(day)
        if pattern is None:
            continue
        model_point = predict_price(pattern, pattern_at, snapshot, horizon)
        if model_point is not None:
            calibration[day][MODEL_METHOD] = max(MIN_POINT, model_point)
    current_pattern = market_pattern(history, origin, horizon, FRESH_DAYS)
    current_model_point = (
        predict_price(current_pattern, pattern_at, history, horizon)
        if current_pattern is not None
        else None
    )
    bands = estimate(history, origin, horizon, calibration, current_model_point)
    if not bands:
        return ForecastView(status="insufficient_data", backtest=[], **context)

    folds: dict[str, list[tuple[Band, Decimal]]] = defaultdict(list)
    paired: dict[str, dict[str, list[tuple[Band, Decimal]]]] = {
        CANDIDATE: defaultdict(list),
        MODEL_METHOD: defaultdict(list),
    }
    evaluated = 0
    for day, snapshot in snapshots.items():
        actual = history[day + delta]
        alternatives = estimate(
            snapshot, day, horizon, calibration, calibration[day].get(MODEL_METHOD)
        )
        if "last_value" not in alternatives:
            continue
        for method, band in alternatives.items():
            folds[method].append((band, actual))
            for candidate, comparable in paired.items():
                if candidate in alternatives:
                    comparable[method].append((band, actual))
        evaluated += 1
        if evaluated == 36:
            break

    results = [
        metrics(method, folds[method])
        for method in (*BASELINES, CANDIDATE, MODEL_METHOD)
        if folds[method]
    ]
    # Compare only baseline forecasts with the same evaluation coverage.
    baseline_choices = [
        metric
        for metric in results
        if metric.method in BASELINES
        and metric.method in bands
        and metric.observations == evaluated
    ]
    if not baseline_choices or evaluated < 6:
        return ForecastView(status="insufficient_data", backtest=results, **context)
    selected = min(baseline_choices, key=lambda item: item.mae_bdt_kg).method
    if not synthetic:
        for method, comparable in paired.items():
            candidate_folds = comparable[method]
            if method not in bands or not candidate_folds:
                continue
            references = [
                metrics(reference, comparable[reference])
                for reference in dict.fromkeys((*BASELINES, selected))
                if len(comparable[reference]) == len(candidate_folds)
            ]
            if len(comparable[selected]) == len(candidate_folds) and passes_gate(
                metrics(method, candidate_folds), references
            ):
                selected = method
    band = bands[selected]
    preview = bands.get(MODEL_METHOD) if synthetic else None
    return ForecastView(
        status="baseline" if selected in BASELINES else "quantile",
        method=selected,
        low_bdt_kg=band.low.quantize(MIN_POINT),
        middle_bdt_kg=band.middle.quantize(MIN_POINT),
        high_bdt_kg=band.high.quantize(MIN_POINT),
        backtest=results,
        model_preview=(
            ModelPreview(
                low_bdt_kg=preview.low.quantize(MIN_POINT),
                middle_bdt_kg=preview.middle.quantize(MIN_POINT),
                high_bdt_kg=preview.high.quantize(MIN_POINT),
            )
            if preview is not None
            else None
        ),
        **context,
    )


def market_forecast(
    db: Session, actor: Profile, series: str, horizon: Horizon
) -> ForecastView:
    origin = today()
    rows = db.execute(
        select(
            prices.c.observed_on,
            prices.c.published_on,
            prices.c.low_bdt_kg,
            prices.c.high_bdt_kg,
            prices.c.synthetic,
        )
        .where(
            approved(actor),
            prices.c.series == series,
            prices.c.observed_on >= origin - timedelta(days=1095),
            prices.c.published_on <= origin,
        )
        .order_by(prices.c.observed_on.desc(), prices.c.id)
        .limit(6000)
    ).all()
    reports = [
        Report(
            row.observed_on, row.published_on, (row.low_bdt_kg + row.high_bdt_kg) / 2
        )
        for row in rows
    ]
    return forecast_series(reports, origin, horizon, bool(rows and rows[0].synthetic))


@router.get("/forecasts", response_model=ForecastView)
def read_forecast(series: SeriesKey, actor: Actor, db: DB, horizon: int = 7):
    if horizon not in (7, 14, 28):
        raise HTTPException(422, "invalid_input")
    return market_forecast(db, actor, series, cast(Horizon, horizon))
