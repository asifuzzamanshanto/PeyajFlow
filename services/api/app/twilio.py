import base64
import hashlib
import hmac
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlsplit

from fastapi import HTTPException, Request
from sqlalchemy import Column, DateTime, String, Table, Text, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.database import metadata

events = Table(
    "provider_events",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("channel", String(12), nullable=False),
    Column("kind", String(30), nullable=False),
    Column("reference", String(64), nullable=False),
    Column("response_xml", Text),
    Column(
        "received_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    ),
)


@dataclass(frozen=True)
class Settings:
    origin: str
    account_sid: str
    auth_token: str


def settings(channel: str) -> Settings | None:
    flag = {"voice": "TELEPHONY_PROVIDER", "sms": "SMS_PROVIDER"}[channel]
    if os.getenv(flag) != "twilio":
        return None
    origin = os.getenv("PUBLIC_API_ORIGIN", "").rstrip("/")
    sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    secret = os.getenv("TWILIO_AUTH_TOKEN", "")
    try:
        url = urlsplit(origin)
        if (
            url.scheme != "https"
            or not url.hostname
            or url.username
            or url.password
            or url.path
            or url.query
            or url.fragment
            or not re.fullmatch(r"AC[0-9a-fA-F]{32}", sid)
            or not secret
        ):
            return None
    except ValueError:
        return None
    return Settings(origin, sid, secret)


def fingerprint(*parts: str) -> str:
    return hashlib.sha256("\0".join(parts).encode()).hexdigest()


def signature(url: str, params: dict[str, list[str]], token: str) -> str:
    message = url + "".join(
        key + value for key in sorted(params) for value in sorted(set(params[key]))
    )
    return base64.b64encode(
        hmac.digest(token.encode(), message.encode(), "sha1")
    ).decode()


def one(params: dict[str, list[str]], key: str, *, default: str | None = None) -> str:
    values = params.get(key)
    if values is None and default is not None:
        return default
    if values is None or len(values) != 1:
        raise HTTPException(400, "provider_callback_invalid")
    return values[0]


async def verified_form(
    request: Request, channel: str
) -> tuple[Settings, dict[str, list[str]]]:
    config = settings(channel)
    if config is None:
        raise HTTPException(404, "provider_disabled")
    supplied = request.headers.get("x-twilio-signature", "")
    if not re.fullmatch(r"[A-Za-z0-9+/]{27}=", supplied):
        raise HTTPException(403, "provider_signature_invalid")
    if (
        request.headers.get("content-type", "").split(";")[0].lower().strip()
        != "application/x-www-form-urlencoded"
    ):
        raise HTTPException(415, "provider_callback_invalid")
    payload = bytearray()
    async for chunk in request.stream():
        if len(payload) + len(chunk) > 12_288:
            raise HTTPException(413, "provider_callback_invalid")
        payload.extend(chunk)
    try:
        pairs = parse_qsl(
            payload.decode("utf-8"),
            keep_blank_values=True,
            strict_parsing=True,
            max_num_fields=64,
            errors="strict",
        )
    except (UnicodeError, ValueError) as error:
        raise HTTPException(400, "provider_callback_invalid") from error
    fields: dict[str, list[str]] = defaultdict(list)
    for key, value in pairs:
        fields[key].append(value)
    # Use the configured public origin and exact path/query bytes, never the forwarded host.
    raw_path = request.scope.get("raw_path", request.url.path.encode("ascii"))
    query = request.scope.get("query_string", b"")
    url = (
        config.origin
        + raw_path.decode("ascii")
        + ("?" + query.decode("ascii") if query else "")
    )
    if not hmac.compare_digest(signature(url, fields, config.auth_token), supplied):
        raise HTTPException(403, "provider_signature_invalid")
    if one(fields, "AccountSid") != config.account_sid:
        raise HTTPException(403, "provider_account_mismatch")
    return config, fields


def record(
    db: Session,
    channel: str,
    kind: str,
    reference: str,
    discriminator: str,
    xml: str | None = None,
) -> tuple[bool, str | None]:
    event_id = fingerprint(channel, kind, reference, discriminator)
    inserted = db.scalar(
        pg_insert(events)
        .values(
            id=event_id,
            channel=channel,
            kind=kind,
            reference=reference,
            response_xml=xml,
        )
        .on_conflict_do_nothing(index_elements=[events.c.id])
        .returning(events.c.id)
    )
    if inserted is not None:
        return True, xml
    return False, db.scalar(
        select(events.c.response_xml).where(events.c.id == event_id)
    )
