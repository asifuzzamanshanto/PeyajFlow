import os
from uuid import uuid4

import pytest
from test_pilot import login, lot_input, new_lot, new_offer, reply
from test_pilot import pilot as pilot

from app.auth import demo_id

pytestmark = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"), reason="requires disposable PostgreSQL"
)


def test_delivery_and_independently_reviewed_settlement(pilot):
    client, _, _ = pilot
    farmer, buyer, stranger, admin = [
        login(client, name) for name in ("farmer", "buyer", "buyer-two", "admin")
    ]
    lot = new_lot(client, farmer)
    offer = new_offer(client, buyer, lot, 200)
    accepted = client.post(
        f"/v1/offers/{offer['id']}/respond", headers=farmer, json=reply(offer)
    )
    order_id = accepted.json()["order_id"]
    path = f"/v1/orders/{order_id}/settlement"
    form = {
        "reference": "BUYER-TEST-TRANSFER",
        "request_key": str(uuid4()),
        "confirm": True,
    }
    assert client.get(path, headers=farmer).json()["status"] == "pending"
    assert client.post(path, headers=buyer, json=form).status_code == 409
    for actor, action in [(farmer, "dispatch"), (buyer, "receive")]:
        delivered = client.post(
            f"/v1/orders/{order_id}/transition",
            headers=actor,
            json={
                "action": action,
                "request_key": str(uuid4()),
                "confirm": True,
            },
        )
        assert delivered.status_code == 200, delivered.text
    assert delivered.json()["status"] == "delivered"
    assert client.get(path, headers=stranger).status_code == 404
    assert client.post(path, headers=farmer, json=form).status_code == 403
    assert (
        client.post(
            path, headers=buyer, json={**form, "status": "verified"}
        ).status_code
        == 422
    )
    report = client.post(path, headers=buyer, json=form)
    assert report.status_code == 201, report.text
    assert report.json()["status"] == "reported"
    assert client.post(path, headers=buyer, json=form).json() == report.json()
    assert (
        client.post(
            path, headers=buyer, json={**form, "reference": "CHANGED-REFERENCE"}
        ).status_code
        == 409
    )
    assert (
        client.post(
            path, headers=buyer, json={**form, "request_key": str(uuid4())}
        ).status_code
        == 409
    )
    assert client.get(path, headers=farmer).json()["status"] == "reported"
    queue = client.get("/v1/admin/settlements", headers=admin)
    assert queue.status_code == 200, queue.text
    assert any(
        item["order_id"] == order_id and item["total_bdt"] == "9110.00"
        for item in queue.json()
    )
    review_path = f"{path}/{report.json()['id']}/review"
    decision = {
        "decision": "rejected",
        "evidence_reference": "INDEPENDENT-CHECK-1",
        "confirm": True,
    }
    assert client.post(review_path, headers=buyer, json=decision).status_code == 403
    assert (
        client.post(
            review_path,
            headers=admin,
            json={**decision, "evidence_reference": form["reference"].lower()},
        ).status_code
        == 422
    )
    assert (
        client.post(review_path, headers=admin, json=decision).json()["status"]
        == "rejected"
    )
    assert client.get(path, headers=farmer).json()["status"] == "pending"
    corrected = client.post(
        path,
        headers=buyer,
        json={
            **form,
            "reference": "BUYER-CORRECTED-REFERENCE",
            "request_key": str(uuid4()),
        },
    )
    assert corrected.status_code == 201, corrected.text
    review_path = f"{path}/{corrected.json()['id']}/review"
    decision = {
        **decision,
        "decision": "verified",
        "evidence_reference": "INDEPENDENT-CHECK-2",
    }
    verified = client.post(review_path, headers=admin, json=decision)
    assert verified.status_code == 200, verified.text
    assert (
        client.post(review_path, headers=admin, json=decision).json() == verified.json()
    )
    for actor in (buyer, farmer):
        settlement = client.get(path, headers=actor).json()
        assert settlement["status"] == "verified"
        assert {row["status"] for row in settlement["reports"]} == {
            "verified",
            "rejected",
        }
        assert "INDEPENDENT-CHECK" not in str(settlement)
        alerts = client.get("/v1/notifications", headers=actor).json()["items"]
        assert (
            sum(
                row["kind"] == "payment.verified" and row["resource_id"] == order_id
                for row in alerts
            )
            == 1
        )
    audit = client.get(
        "/v1/admin/audit",
        headers=admin,
        params={"action": "payment.", "resource_id": order_id},
    )
    assert {row["action"] for row in audit.json()["items"]} == {
        "payment.reported",
        "payment.rejected",
        "payment.verified",
    }
    assert "REFERENCE" not in audit.text and "INDEPENDENT-CHECK" not in audit.text
    stock = client.get(f"/v1/lots/{lot}", headers=farmer).json()
    assert stock["available_kg"] == "800.000" and stock["reserved_kg"] == "0.000"


def test_farmer_grants_and_revokes_agent_stock_access(pilot):
    client, _, _ = pilot
    farmer, agent, buyer, admin = [
        login(client, name) for name in ("farmer-two", "agent", "buyer", "admin")
    ]
    agent_id = demo_id("membership", "agent")
    farmer_id = demo_id("membership", "farmer-two")
    path = f"/v1/delegations/{agent_id}"
    register = f"/v1/lots/delegated/{farmer_id}"
    lot = lot_input(listed=False)
    assert client.post(register, headers=agent, json=lot).status_code == 404
    assert client.put(path, headers=buyer).status_code == 403
    assert client.put(f"/v1/delegations/{farmer_id}", headers=farmer).status_code == 404
    assert client.put(path, headers=farmer).status_code == 204
    assert client.put(path, headers=farmer).status_code == 204
    assert any(
        row["membership_id"] == str(farmer_id)
        for row in client.get("/v1/delegations", headers=agent).json()
    )
    assert (
        client.post(register, headers=agent, json={**lot, "listed": True}).status_code
        == 422
    )
    created = client.post(register, headers=agent, json=lot)
    assert created.status_code == 201, created.text
    assert (
        client.post(register, headers=agent, json=lot).json()["id"]
        == created.json()["id"]
    )
    lot_path = f"/v1/lots/{created.json()['id']}"
    assert client.get(lot_path, headers=farmer).json()["listed"] is False
    assistance = {
        "kind": "inspection",
        "lot_id": created.json()["id"],
        "note": "Inspect the delegated lot",
    }
    assert (
        client.post("/v1/voice/tasks", headers=buyer, json=assistance).status_code
        == 403
    )
    task = client.post("/v1/voice/tasks", headers=farmer, json=assistance)
    assert task.status_code == 201, task.text
    assert task.json()["can_resolve"] is False
    task_id = task.json()["id"]
    resolve = f"/v1/voice/tasks/{task_id}/resolve"
    assert client.post(resolve, headers=farmer).status_code == 403
    assert any(
        row["id"] == task_id and row["can_resolve"]
        for row in client.get("/v1/voice/tasks", headers=agent).json()
    )
    assert client.post(resolve, headers=agent).json()["status"] == "resolved"
    assert client.post(resolve, headers=agent).json()["status"] == "resolved"
    assert (
        client.patch(
            lot_path,
            headers=agent,
            json={
                key: value
                for key, value in lot.items()
                if key not in {"quantity", "unit", "request_key"}
            },
        ).status_code
        == 403
    )
    assert client.delete(path, headers=farmer).status_code == 204
    assert client.delete(path, headers=farmer).status_code == 204
    assert client.get(lot_path, headers=agent).status_code == 404
    assert client.post(resolve, headers=agent).status_code == 404
    assert client.get(lot_path, headers=farmer).status_code == 200
    audit = client.get(
        "/v1/admin/audit",
        headers=admin,
        params={"action": "delegation.", "resource_id": str(agent_id)},
    ).json()
    assert {row["action"] for row in audit["items"]} >= {
        "delegation.granted",
        "delegation.revoked",
    }
