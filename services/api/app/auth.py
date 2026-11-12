import os
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from hashlib import sha256
from secrets import token_urlsafe
from typing import Annotated, Literal
from uuid import UUID, uuid4, uuid5

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, StringConstraints
from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    Uuid,
    delete,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.database import DB, metadata
from app.rate_limits import enforce


class Role(StrEnum):
    FARMER = "farmer"
    BUYER = "buyer"
    AGENT = "agent"
    ADMIN = "admin"


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


ShortText = Annotated[str, StringConstraints(min_length=1, max_length=100)]
router = APIRouter(prefix="/v1", tags=["Identity"])
bearer = HTTPBearer(auto_error=False)
TOKEN_TTL = timedelta(hours=8)

users = Table(
    "users",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid4),
    Column("name", String(100), nullable=False),
    Column("district", String(100), nullable=False),
    Column("language", String(2), nullable=False),
    Column("demo_key", String(32), unique=True),
    Column("verified", Boolean, nullable=False, default=False),
)
organizations = Table(
    "organizations",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid4),
    Column("name", String(100), nullable=False),
    Column("is_demo", Boolean, nullable=False, default=False),
)
memberships = Table(
    "memberships",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid4),
    Column("user_id", ForeignKey("users.id"), nullable=False, index=True),
    Column("organization_id", ForeignKey("organizations.id"), nullable=False),
    Column("role", String(12), nullable=False),
    CheckConstraint(
        "role in ('farmer', 'buyer', 'agent', 'admin')", name="membership_role"
    ),
)
sessions = Table(
    "sessions",
    metadata,
    Column("token_hash", String(64), primary_key=True),
    Column("membership_id", ForeignKey("memberships.id"), nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False, index=True),
)
delegations = Table(
    "delegations",
    metadata,
    Column("farmer_membership_id", ForeignKey("memberships.id"), primary_key=True),
    Column("agent_membership_id", ForeignKey("memberships.id"), primary_key=True),
)
audit_log = Table(
    "audit_log",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid4),
    Column("membership_id", ForeignKey("memberships.id"), nullable=False),
    Column("action", String(60), nullable=False),
    Column("resource_id", Uuid, nullable=False, index=True),
    Column("context", JSON, nullable=False, default=dict),
    Column(
        "recorded_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    ),
)


class Profile(BaseModel):
    user_id: UUID
    membership_id: UUID
    organization_id: UUID
    organization: str
    name: str
    district: str
    language: Literal["bn", "en"]
    role: Role
    verified: bool
    is_demo: bool


class ProfileEdit(Input):
    name: ShortText
    district: ShortText
    language: Literal["bn", "en"]


class DemoLogin(Input):
    identity: Annotated[str, StringConstraints(max_length=32)]


class DemoIdentity(BaseModel):
    identity: str
    name: str
    role: Role


class SessionToken(BaseModel):
    token: str
    expires_at: datetime


def demo_enabled() -> bool:
    return (
        os.getenv("APP_ENV") in {"development", "test"}
        and os.getenv("DEMO_MODE") == "true"
    )


DEMO_MEMBERS = {
    "farmer": ("Rahim · Pabna", "Pabna", Role.FARMER, False),
    "farmer-two": ("Salma · Pabna", "Pabna", Role.FARMER, False),
    "buyer": ("Nadia · Dhaka", "Dhaka", Role.BUYER, True),
    "buyer-two": ("Hasan · Dhaka", "Dhaka", Role.BUYER, False),
    "agent": ("Jalil · Pabna", "Pabna", Role.AGENT, True),
    "admin": ("Demo operator", "Dhaka", Role.ADMIN, True),
}
DEMO_NAMESPACE = UUID("15e4a3fb-cb8f-4da0-9b72-686ed8bf45ce")


def demo_id(kind: str, identity: str) -> UUID:
    return uuid5(DEMO_NAMESPACE, f"{kind}:{identity}")


def seed_demo(db: Session) -> None:
    for key, (name, district, role, verified) in DEMO_MEMBERS.items():
        user_id = demo_id("user", key)
        organization_id = demo_id("organization", key)
        db.execute(
            pg_insert(users)
            .values(
                id=user_id,
                name=name,
                district=district,
                language="bn",
                demo_key=key,
                verified=verified,
            )
            .on_conflict_do_nothing()
        )
        db.execute(
            pg_insert(organizations)
            .values(
                id=organization_id,
                name=name,
                is_demo=True,
            )
            .on_conflict_do_nothing()
        )
        db.execute(
            pg_insert(memberships)
            .values(
                id=demo_id("membership", key),
                user_id=user_id,
                organization_id=organization_id,
                role=role,
            )
            .on_conflict_do_nothing()
        )
    db.execute(
        pg_insert(delegations)
        .values(
            farmer_membership_id=demo_id("membership", "farmer"),
            agent_membership_id=demo_id("membership", "agent"),
        )
        .on_conflict_do_nothing()
    )


def fingerprint(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def actor_for(
    db: DB,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Profile:
    if credentials is None or len(credentials.credentials) != 43:
        raise HTTPException(401, "sign_in_required")
    row = (
        db.execute(
            select(
                users.c.id.label("user_id"),
                memberships.c.id.label("membership_id"),
                organizations.c.id.label("organization_id"),
                organizations.c.name.label("organization"),
                users.c.name,
                users.c.district,
                users.c.language,
                memberships.c.role,
                users.c.verified,
                organizations.c.is_demo,
            )
            .select_from(sessions.join(memberships).join(users).join(organizations))
            .where(
                sessions.c.token_hash == fingerprint(credentials.credentials),
                sessions.c.expires_at > func.now(),
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None or (row["is_demo"] and not demo_enabled()):
        raise HTTPException(401, "session_expired")
    if os.getenv("APP_ENV") == "production":
        enforce(db, "member", str(row["membership_id"]), limit=120, seconds=60)
    return Profile.model_validate(row)


Actor = Annotated[Profile, Depends(actor_for)]


def require_role(actor: Profile, *roles: Role) -> None:
    if actor.role not in roles:
        raise HTTPException(403, "role_forbidden")


def audit(
    db: Session, actor: Profile, action: str, resource_id: UUID, **context: str
) -> None:
    db.execute(
        insert(audit_log).values(
            membership_id=actor.membership_id,
            action=action,
            resource_id=resource_id,
            context=context,
        )
    )


@router.get("/auth/demo", response_model=list[DemoIdentity])
def demo_identities() -> list[DemoIdentity]:
    if not demo_enabled():
        raise HTTPException(404, "demo_disabled")
    return [
        DemoIdentity(identity=identity, name=name, role=role)
        for identity, (name, _, role, _) in DEMO_MEMBERS.items()
    ]


@router.post("/auth/demo", response_model=SessionToken, status_code=201)
def demo_login(body: DemoLogin, db: DB, response: Response) -> SessionToken:
    if not demo_enabled():
        raise HTTPException(404, "demo_disabled")
    if body.identity not in DEMO_MEMBERS:
        raise HTTPException(422, "unknown_demo_identity")
    member_id = demo_id("membership", body.identity)
    if (
        db.get_bind() is None
        or db.scalar(select(memberships.c.id).where(memberships.c.id == member_id))
        is None
    ):
        raise HTTPException(503, "demo_seed_required")
    return issue_token(db, member_id, response)


def issue_token(db: Session, member_id: UUID, response: Response) -> SessionToken:
    token = token_urlsafe(32)
    expires_at = datetime.now(UTC) + TOKEN_TTL
    db.execute(delete(sessions).where(sessions.c.expires_at <= func.now()))
    db.execute(
        insert(sessions).values(
            token_hash=fingerprint(token),
            membership_id=member_id,
            expires_at=expires_at,
        )
    )
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return SessionToken(token=token, expires_at=expires_at)


@router.get("/me", response_model=Profile)
def me(actor: Actor) -> Profile:
    return actor


@router.patch("/me", response_model=Profile)
def edit_profile(body: ProfileEdit, actor: Actor, db: DB) -> Profile:
    db.execute(
        update(users).where(users.c.id == actor.user_id).values(**body.model_dump())
    )
    audit(db, actor, "profile.updated", actor.user_id)
    db.commit()
    return actor.model_copy(update=body.model_dump())


@router.delete("/auth/session", status_code=204)
def logout(
    db: DB,
    actor: Actor,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Response:
    assert credentials is not None
    db.execute(
        delete(sessions).where(
            sessions.c.token_hash == fingerprint(credentials.credentials)
        )
    )
    db.commit()
    return Response(status_code=204)
