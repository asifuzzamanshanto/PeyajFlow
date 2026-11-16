from bisect import bisect_right
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from math import cos, dist, exp, log, sin, tau
from statistics import mean

MODEL_METHOD = "lagged_price_neighbors"
MIN_TRAINING_ROWS = 24
NEIGHBORS = 7


@dataclass(frozen=True)
class MarketPattern:
    price: Decimal
    features: tuple[float, ...]


def market_pattern(
    history: dict[date, Decimal], origin: date, horizon: int, fresh_days: int
) -> MarketPattern | None:
    if not history:
        return None
    days = list(history)
    latest = days[-1]
    if (origin - latest).days > fresh_days:
        return None
    price = history[latest]
    changes = []
    for lag in (7, 14, 28):
        lag_day = latest - timedelta(days=lag)
        index = bisect_right(days, lag_day) - 1
        if index < 0 or (lag_day - days[index]).days > 7:
            return None
        changes.append(log(float(price / history[days[index]])))
    angle = tau * (origin.toordinal() + horizon) / 365.2425
    return MarketPattern(price, (*changes, 0.05 * sin(angle), 0.05 * cos(angle)))


def predict_price(
    pattern: MarketPattern,
    pattern_at: Callable[[date], MarketPattern | None],
    history: dict[date, Decimal],
    horizon: int,
) -> Decimal | None:
    delta = timedelta(days=horizon)
    # Each example is a prior forecast matched to a target price known by this cutoff.
    examples = []
    previous = None
    for target in reversed(history):
        if previous is not None and (previous - target).days < 7:
            continue
        past = pattern_at(target - delta)
        if past is None:
            continue
        examples.append((past.features, log(float(history[target] / past.price))))
        previous = target
        if len(examples) == 78:
            break
    if len(examples) < MIN_TRAINING_ROWS:
        return None
    nearest = sorted(examples, key=lambda item: dist(pattern.features, item[0]))[
        :NEIGHBORS
    ]
    return pattern.price * Decimal(str(exp(mean(change for _, change in nearest))))
