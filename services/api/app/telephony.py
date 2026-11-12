import os
import re
from typing import Annotated
from urllib.parse import urlsplit
from xml.etree.ElementTree import Element, SubElement, tostring

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import Column, DateTime, String, Table, func, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app import twilio
from app.database import DB, metadata

PATH = "/v1/webhooks/telephony/twilio"
router = APIRouter(prefix=PATH, tags=["Carrier callbacks"])
calls = Table(
    "carrier_calls",
    metadata,
    Column("reference", String(64), primary_key=True),
    Column("status", String(16), nullable=False),
    Column(
        "updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
)
ACTIVE = ("queued", "ringing", "in-progress")
TERMINAL = ("completed", "busy", "failed", "no-answer", "canceled")


async def verify_voice(request: Request):
    return await twilio.verified_form(request, "voice")


Callback = Annotated[
    tuple[twilio.Settings, dict[str, list[str]]], Depends(verify_voice)
]


def reference(fields: dict[str, list[str]]) -> str:
    sid = twilio.one(fields, "CallSid")
    if not re.fullmatch(r"CA[0-9a-fA-F]{32}", sid):
        raise HTTPException(400, "provider_callback_invalid")
    return twilio.fingerprint(sid)


def greeting(response: Element) -> None:
    audio = os.getenv("TWILIO_VOICE_GREETING_URL", "")
    try:
        url = urlsplit(audio)
        valid = (
            url.scheme == "https"
            and url.hostname
            and not url.username
            and not url.password
        )
    except ValueError:
        valid = False
    if valid:
        SubElement(response, "Play").text = audio
    else:
        SubElement(
            response, "Say", language="en-US"
        ).text = (
            "Welcome to PeyajFlow. Press one for the service overview, or two for help."
        )


def response_xml(root: Element) -> str:
    return tostring(root, encoding="unicode", short_empty_elements=True)


@router.post("")
def incoming(callback: Callback, db: DB):
    config, fields = callback
    call = reference(fields)
    root = Element("Response")
    menu = SubElement(
        root,
        "Gather",
        input="dtmf",
        numDigits="1",
        timeout="6",
        action=f"{config.origin}{PATH}/menu",
        method="POST",
        actionOnEmptyResult="true",
    )
    greeting(menu)
    SubElement(root, "Hangup")
    _, xml = twilio.record(db, "voice", "incoming", call, "start", response_xml(root))
    db.execute(
        pg_insert(calls)
        .values(reference=call, status="in-progress")
        .on_conflict_do_nothing(index_elements=[calls.c.reference])
    )
    db.commit()
    return Response(xml, media_type="application/xml")


@router.post("/menu")
def menu_result(callback: Callback, db: DB):
    _, fields = callback
    call = reference(fields)
    digit = twilio.one(fields, "Digits", default="")
    root = Element("Response")
    text = {
        "1": "PeyajFlow helps manage onion stock, offers, and orders. Use the signed-in workspace to act on an order.",
        "2": "Open the PeyajFlow workspace to contact an operator.",
    }.get(digit, "Please use the PeyajFlow workspace for help.")
    SubElement(root, "Say", language="en-US").text = text
    SubElement(root, "Hangup")
    _, xml = twilio.record(db, "voice", "menu", call, "selection", response_xml(root))
    db.commit()
    return Response(xml, media_type="application/xml")


@router.post("/status", status_code=204)
def status(callback: Callback, db: DB):
    _, fields = callback
    call = reference(fields)
    state = twilio.one(fields, "CallStatus")
    if state not in (*ACTIVE, *TERMINAL):
        raise HTTPException(400, "provider_callback_invalid")
    first, _ = twilio.record(db, "voice", f"status.{state}", call, "state")
    if first:
        result = db.scalar(
            pg_insert(calls)
            .values(reference=call, status=state)
            .on_conflict_do_nothing(index_elements=[calls.c.reference])
            .returning(calls.c.reference)
        )
        if result is None:
            predecessors = (
                ACTIVE if state in TERMINAL else ACTIVE[: ACTIVE.index(state)]
            )
            if predecessors:
                db.execute(
                    update(calls)
                    .where(calls.c.reference == call, calls.c.status.in_(predecessors))
                    .values(status=state, updated_at=func.now())
                )
    db.commit()
