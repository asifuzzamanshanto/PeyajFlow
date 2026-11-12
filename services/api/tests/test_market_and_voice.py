import csv
import os
from datetime import timedelta
from decimal import Decimal
from io import StringIO
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from sqlalchemy import update
from sqlalchemy.orm import Session
from test_pilot import login, new_lot, new_offer, reply
from test_pilot import pilot as pilot

from app import advice
from app.forecast import ForecastView, Report, available, forecast_series
from app.logistics import quotes
from app.lots import today
from app.market_data import CSV_FIELDS
from app.trade import now
from app.voice import actions


def observation(market, offset=0, **changes):
    day = (today() - timedelta(days=offset)).isoformat()
    return {
        "observed_on": day,
        "published_on": day,
        "district": "Pabna",
        "market": market,
        "price_type": "farmgate",
        "grade": "A",
        "unit": "kg",
        "kg_per_maund": "",
        "low": "35",
        "high": "40",
        "source_url": "https://example.invalid/verification",
        "source_record": "fixture-row",
        **changes,
    }


def batch_payload(rows, synthetic=True):
    value = StringIO()
    writer = csv.DictWriter(value, fieldnames=CSV_FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    return {
        "label": "Local test batch",
        "synthetic": synthetic,
        "csv": value.getvalue(),
    }


requires_database = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"),
    reason="requires disposable migrated PostgreSQL",
)


@requires_database
def test_import_review_dedup_units_staleness_and_access(pilot):
    client, _, _ = pilot
    admin, farmer = login(client, "admin"), login(client, "farmer")
    market = f"Import {uuid4().hex}"
    valid = observation(
        market, unit="maund", kg_per_maund="40", low="1400", high="1600"
    )
    rows = [
        valid,
        valid,
        observation(market, 15),
        observation(market, 1, low="50", high="20"),
    ]
    base = "/v1/admin/data-imports"
    assert (
        client.post(base, headers=farmer, json=batch_payload(rows)).status_code == 403
    )
    imported = client.post(base, headers=admin, json=batch_payload(rows))
    assert imported.status_code == 201, imported.text
    batch = imported.json()
    assert batch["status"] == "pending"
    assert batch["accepted_rows"] == 2 and batch["duplicates"] == 1
    assert [item["line"] for item in batch["errors"]] == [3, 5]
    path = f"{base}/{batch['id']}"
    preview = client.get(path, headers=admin).json()
    series = preview["observations"][0]["series"]
    assert client.get(path, headers=farmer).status_code == 403
    assert (
        client.get(
            "/v1/market/prices", headers=farmer, params={"series": series}
        ).json()
        == []
    )
    assert (
        client.post(
            f"{path}/review", headers=admin, json={"decision": "approved"}
        ).status_code
        == 200
    )
    actual = client.get(
        "/v1/market/prices", headers=farmer, params={"series": series}
    ).json()
    assert len(actual) == 2 and all(row["synthetic"] for row in actual)
    assert (
        Decimal(actual[0]["low_bdt_kg"]) == 35
        and Decimal(actual[0]["high_bdt_kg"]) == 40
    )
    assert (
        actual[0]["source_record"] == "fixture-row"
        and actual[1]["stale"]
        and not actual[0]["stale"]
    )
    outlook = client.get(
        "/v1/market/forecasts", headers=farmer, params={"series": series, "horizon": 14}
    )
    assert (
        outlook.status_code == 200 and outlook.json()["status"] == "insufficient_data"
    )
    second = client.post(base, headers=admin, json=batch_payload([valid])).json()
    assert second["status"] == "rejected" and second["duplicates"] == 1
    assert (
        client.post(
            base, headers=admin, json={**batch_payload([]), "csv": "foo,bar\na,b"}
        ).status_code
        == 422
    )


def test_walk_forward_forecast_and_publication_date():
    origin = today()
    reports = [
        Report(
            origin - timedelta(weeks=103 - i),
            origin - timedelta(weeks=103 - i),
            Decimal(34 + i // 3 + i % 9),
        )
        for i in range(104)
    ]
    hidden = Report(
        origin - timedelta(days=7), origin + timedelta(days=1), Decimal("9000")
    )
    assert available([hidden], origin) == {}
    baseline = forecast_series(reports, origin, 14, True)
    assert baseline == forecast_series([*reports, hidden], origin, 14, True)
    assert baseline.status == "baseline" and baseline.synthetic
    assert baseline.low_bdt_kg <= baseline.middle_bdt_kg <= baseline.high_bdt_kg
    assert any(metric.observations == 36 for metric in baseline.backtest)
    assert (
        forecast_series(reports, origin + timedelta(days=8), 7, False).status == "stale"
    )
    assert forecast_series(reports[-6:], origin, 7, False).status == "insufficient_data"


def test_quantile_gate_promotes_only_eligible_real_series():
    origin = today()
    increments = [0, 1, 1, 2, 2, 2, 3, 3, 4, 6]
    price = Decimal(35)
    reports = []
    for index in range(130):
        day = origin - timedelta(weeks=129 - index)
        price += increments[index % len(increments)]
        reports.append(Report(day, day, price))
    assert forecast_series(reports, origin, 7, False).status == "quantile"
    assert forecast_series(reports, origin, 7, True).status == "baseline"


@requires_database
def test_hold_sell_comparison_and_abstention(pilot, monkeypatch):
    client, _, _ = pilot
    farmer, buyer, admin = [
        login(client, name) for name in ("farmer", "buyer", "admin")
    ]
    lot = new_lot(client, farmer)
    path = f"/v1/lots/{lot}/recommendation"
    inputs = {
        "manual_price_bdt_kg": "50",
        "quantity_kg": "200",
        "hypothetical_low": "45",
        "hypothetical_middle": "50",
        "hypothetical_high": "55",
        "loss_pct": "10",
        "fees_now_bdt": "500",
        "storage_bdt": "1000",
        "assumptions_reviewed": True,
    }
    result = client.post(path, headers=farmer, json=inputs).json()
    assert result["recommendation"] == "INSUFFICIENT_DATA"
    assert result["sell_now_net_bdt"] == "9500.00"
    assert [result[f"hold_{key}_bdt"] for key in ("low", "middle", "high")] == [
        "7100.00",
        "8000.00",
        "8900.00",
    ]
    loss = client.post(
        path, headers=farmer, json={**inputs, "storage_bdt": "20000"}
    ).json()
    assert (
        Decimal(loss["hold_low_bdt"]) < 0
        and loss["recommendation"] == "INSUFFICIENT_DATA"
    )
    market = f"Farmgate {uuid4().hex}"
    batch = client.post(
        "/v1/admin/data-imports",
        headers=admin,
        json=batch_payload(
            [observation(market)],
            synthetic=False,
        ),
    ).json()
    batch_path = f"/v1/admin/data-imports/{batch['id']}"
    series = client.get(batch_path, headers=admin).json()["observations"][0]["series"]
    client.post(f"{batch_path}/review", headers=admin, json={"decision": "approved"})
    offer = new_offer(client, buyer, lot, 200)
    monkeypatch.setattr(advice, "lot_risk", lambda *args: SimpleNamespace(band="low"))

    def outlook(*args):
        return ForecastView(
            status="baseline",
            method="last_value",
            horizon_days=7,
            synthetic=False,
            as_of=today(),
            target_on=today() + timedelta(days=7),
            history_count=80,
            low_bdt_kg=Decimal(20),
            middle_bdt_kg=Decimal(25),
            high_bdt_kg=Decimal(30),
            backtest=[],
        )

    monkeypatch.setattr(advice, "market_forecast", outlook)
    result = client.post(
        path,
        headers=farmer,
        json={
            "offer_id": offer["id"],
            "series": series,
            "assumptions_reviewed": True,
        },
    ).json()
    assert result["recommendation"] == "SELL_PART"
    assert (
        result["quantity_kg"] == "200.000"
        and result["sale_now_source"] == "verified_buyer_offer"
    )


def make_order(client, farmer, buyer, lot):
    offer = new_offer(client, buyer, lot, 200, price_bdt_kg="45")
    accepted = client.post(
        f"/v1/offers/{offer['id']}/respond", headers=farmer, json=reply(offer)
    )
    assert accepted.status_code == 200, accepted.text
    return accepted.json()["order_id"]


@requires_database
def test_ranked_matching_and_quote_booking(pilot):
    client, engine, _ = pilot
    farmer, buyer, admin, outsider = [
        login(client, name) for name in ("farmer", "buyer", "admin", "buyer-two")
    ]
    variety = f"Match-{uuid4().hex}"
    full = new_lot(client, farmer, district="Pabna", variety=variety)
    partial = new_lot(client, farmer, district="Natore", variety=variety, quantity="80")
    demand = client.post(
        "/v1/buyer-requests",
        headers=buyer,
        json={
            "quantity_kg": "200",
            "variety": variety,
            "minimum_grade": "B",
            "transport": "buyer",
            "delivery_district": "Dhaka",
            "delivery_from": today().isoformat(),
            "delivery_to": today().isoformat(),
        },
    ).json()
    params = {
        "request_id": demand["id"],
        "ranked": True,
        "preferred_district": "Natore",
    }
    ranked = client.get("/v1/matches", headers=buyer, params=params)
    assert ranked.status_code == 200, ranked.text
    assert [row["id"] for row in ranked.json()["items"]] == [full, partial]
    assert "estimated_landed_bdt" not in ranked.json()["items"][0]
    estimates = client.get(
        "/v1/matches",
        headers=buyer,
        params={
            **params,
            "price_assumption_bdt_kg": "45",
            "preferred_freight_bdt": "100",
            "other_freight_bdt": "500",
        },
    ).json()["items"]
    assert (
        estimates[0]["coverage"] == "full"
        and estimates[0]["estimated_landed_bdt"] == "9500.00"
    )
    assert (
        estimates[1]["coverage"] == "partial"
        and estimates[1]["estimated_landed_bdt"] == "3700.00"
    )
    order = make_order(client, farmer, buyer, full)
    path = "/v1/logistics/quote-requests"
    body = {
        "order_id": order,
        "pickup_on": today().isoformat(),
        "handling": "Bagged",
        "request_key": str(uuid4()),
    }
    assert client.post(path, headers=farmer, json=body).status_code == 403
    assert client.post(path, headers=outsider, json=body).status_code == 404
    opened = client.post(path, headers=buyer, json=body)
    assert opened.status_code == 201, opened.text
    request = opened.json()["id"]
    assert client.post(path, headers=buyer, json=body).json()["id"] == request
    terms = {
        "provider": "Test carrier",
        "source_ref": "fixture-1",
        "pickup_on": today().isoformat(),
        "capacity_kg": "200",
        "freight_bdt": "450",
        "handling_bdt": "50",
    }
    assert (
        client.post(
            f"{path}/{request}/quotes",
            headers=admin,
            json={**terms, "capacity_kg": "199"},
        ).status_code
        == 422
    )
    recorded = client.post(f"{path}/{request}/quotes", headers=admin, json=terms)
    assert recorded.status_code == 201, recorded.text
    quote = recorded.json()
    assert (
        quote["buyer_landed_bdt"] == "9500.00"
        and quote["seller_net_before_other_costs_bdt"] == "9000.00"
    )
    assert (
        client.post(
            f"{path}/{request}/book",
            headers=buyer,
            json={"quote_id": quote["id"], "confirm": True},
        ).json()["status"]
        == "booked"
    )
    with Session(engine) as db, db.begin():
        db.execute(
            update(quotes)
            .where(quotes.c.id == UUID(quote["id"]))
            .values(valid_until=now() - timedelta(seconds=1))
        )
    parity = client.get(f"/v1/orders/{order}/logistics", headers=farmer).json()
    assert parity["requests"][0]["booked_quote_id"] == quote["id"]


@requires_database
def test_call_wrong_lot_timeout_disconnect_and_atomic_replay(pilot):
    client, engine, _ = pilot
    farmer, buyer, outsider, agent = [
        login(client, name) for name in ("farmer", "buyer", "farmer-two", "agent")
    ]
    lot = new_lot(client, farmer, quantity="25", unit="maund", kg_per_maund="40")
    offer = new_offer(client, buyer, lot, 200, price_bdt_kg="45")
    params = {"offer_id": offer["id"], "lot_id": lot, "version": offer["version"]}
    start = "/v1/voice/calls"

    def new_call():
        return f"{start}/{client.post(start, headers=farmer).json()['id']}"

    def prepare(path, args=params, phrase="অফার গ্রহণ"):
        return client.post(
            f"{path}/intent",
            headers=farmer,
            json={"phrase": phrase, "params": args},
        )

    def code(path, staged):
        return {"action_id": staged["entry"]["id"], "digits": staged["demo_code"]}

    path = new_call()
    assert client.get(path, headers=outsider).status_code == 404
    assert (
        client.post(
            f"{path}/intent", headers=farmer, json={"phrase": "অজানা"}
        ).status_code
        == 422
    )
    assert (
        prepare(path, {**params, "lot_id": str(uuid4())}).json()["detail"]
        == "voice_wrong_lot"
    )
    assert (
        prepare(path, phrase="অফার গ্রহণ ১০ কেজি").json()["detail"]
        == "voice_quantity_mismatch"
    )
    staged = prepare(path, phrase="অফার গ্রহণ ৫ মণ").json()
    assert "9000.00" in staged["entry"]["readback_bn"]
    assert "5.000 মণ" in staged["entry"]["readback_bn"]
    assert (
        client.get(f"/v1/lots/{lot}", headers=farmer).json()["reserved_kg"] == "0.000"
    )
    invalid = "0000" if staged["demo_code"] != "0000" else "0001"
    assert (
        client.post(
            f"{path}/confirm",
            headers=farmer,
            json={**code(path, staged), "digits": invalid},
        ).status_code
        == 422
    )
    assert client.delete(path, headers=farmer).status_code == 204
    assert (
        client.post(
            f"{path}/confirm", headers=farmer, json=code(path, staged)
        ).status_code
        == 409
    )
    path = new_call()
    staged = prepare(path).json()
    with Session(engine) as db, db.begin():
        db.execute(
            update(actions)
            .where(actions.c.id == UUID(staged["entry"]["id"]))
            .values(expires_at=now() - timedelta(seconds=1))
        )
    assert (
        client.post(
            f"{path}/confirm", headers=farmer, json=code(path, staged)
        ).status_code
        == 409
    )
    assert (
        client.get(f"/v1/lots/{lot}", headers=farmer).json()["reserved_kg"] == "0.000"
    )
    staged = prepare(path).json()
    confirmation = code(path, staged)
    confirmation["digits"] = confirmation["digits"].translate(
        str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
    )
    result = client.post(f"{path}/confirm", headers=farmer, json=confirmation).json()
    assert result["state"] == "committed"
    assert (
        client.post(f"{path}/confirm", headers=farmer, json=confirmation).json()[
            "result"
        ]
        == result["result"]
    )
    order = result["result"]["order_id"]
    assert (
        client.get(f"/v1/orders/{order}", headers=buyer).json()["offer"]["lot_id"]
        == lot
    )
    assert (
        client.get(f"/v1/lots/{lot}", headers=farmer).json()["reserved_kg"] == "200.000"
    )
    task = client.post(
        f"{path}/intent",
        headers=farmer,
        json={
            "phrase": "পরিদর্শন চাই",
            "params": {"lot_id": lot, "note": "Check storage shed"},
        },
    ).json()
    completed = client.post(
        f"{path}/confirm", headers=farmer, json=code(path, task)
    ).json()
    task_id = completed["result"]["task_id"]
    assert any(
        row["id"] == task_id
        for row in client.get("/v1/voice/tasks", headers=agent).json()
    )
    assert (
        client.post(f"/v1/voice/tasks/{task_id}/resolve", headers=agent).json()[
            "status"
        ]
        == "resolved"
    )
