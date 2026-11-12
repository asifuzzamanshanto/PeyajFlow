import argparse
import getpass
import hmac
import re
import secrets
from datetime import UTC, datetime
from hashlib import scrypt
from threading import BoundedSemaphore
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import Field, SecretStr, StringConstraints
from sqlalchemy import Column, ForeignKey, String, Table, delete, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import (
    Input,
    Role,
    SessionToken,
    issue_token,
    memberships,
    organizations,
    sessions,
    users,
)
from app.database import DB, database_engine, metadata
from app.notifications import contacts
from app.rate_limits import enforce

router = APIRouter(prefix="/v1/auth", tags=["Identity"])
USERNAME = r"^[a-zA-Z][a-zA-Z0-9_.-]{2,63}$"
PHONE = r"^\+[1-9][0-9]{7,14}$"
DUMMY = f"{'0' * 32}:{'0' * 64}"
KDF_SLOTS = BoundedSemaphore(2)
credentials = Table(
    "account_credentials",
    metadata,
    Column("username", String(64), primary_key=True),
    Column("membership_id", ForeignKey("memberships.id"), unique=True, nullable=False),
    Column("password_digest", String(97), nullable=False),
)


class Login(Input):
    username: Annotated[str, StringConstraints(pattern=USERNAME)]
    password: Annotated[SecretStr, Field(min_length=1, max_length=256)]


def derive(password: str, salt: bytes) -> bytes:
    return scrypt(
        password.encode(), salt=salt, n=2**15, r=8, p=3, dklen=32, maxmem=64 * 1024**2
    )


def password_digest(password: str) -> str:
    if not 14 <= len(password) <= 256:
        raise ValueError("Use a passphrase between 14 and 256 characters.")
    salt = secrets.token_bytes(16)
    return f"{salt.hex()}:{derive(password, salt).hex()}"


@router.post("/password", response_model=SessionToken, status_code=201)
def sign_in(body: Login, request: Request, response: Response, db: DB):
    username = body.username.casefold()
    client = request.client.host if request.client else "unknown"
    enforce(db, "sign-in-client", client, limit=100, seconds=300)
    enforce(db, "sign-in-account", username, limit=8, seconds=900)
    row = (
        db.execute(
            select(credentials)
            .select_from(credentials.join(memberships).join(organizations))
            .where(
                credentials.c.username == username, organizations.c.is_demo.is_(False)
            )
            .with_for_update(read=True, of=credentials)
        )
        .mappings()
        .one_or_none()
    )
    salt, expected = (row["password_digest"] if row else DUMMY).split(":")
    if not KDF_SLOTS.acquire(blocking=False):
        raise HTTPException(429, "rate_limited", headers={"Retry-After": "2"})
    try:
        correct = hmac.compare_digest(
            derive(body.password.get_secret_value(), bytes.fromhex(salt)).hex(),
            expected,
        )
    finally:
        KDF_SLOTS.release()
    if row is None or not correct:
        raise HTTPException(401, "credentials_invalid")
    return issue_token(db, row["membership_id"], response)


def provision(
    db: Session,
    username: str,
    password: str,
    *,
    role: Role,
    name: str,
    district: str,
    organization: str,
    phone: str | None = None,
) -> None:
    if not re.fullmatch(USERNAME, username) or any(
        not 1 <= len(value.strip()) <= 100 for value in (name, district, organization)
    ):
        raise ValueError(
            "Use a valid account ID, display name, district and organization."
        )
    if phone is not None and not re.fullmatch(PHONE, phone):
        raise ValueError("Use an E.164 phone number.")
    key = username.casefold()
    if db.get_bind() is None or db.scalar(
        select(credentials.c.username).where(credentials.c.username == key)
    ):
        raise ValueError("This account ID already exists.")
    member_id, user_id, org_id = uuid4(), uuid4(), uuid4()
    db.execute(
        insert(users).values(
            id=user_id,
            name=name.strip(),
            district=district.strip(),
            language="bn",
            verified=role == Role.ADMIN,
        )
    )
    db.execute(
        insert(organizations).values(
            id=org_id, name=organization.strip(), is_demo=False
        )
    )
    db.execute(
        insert(memberships).values(
            id=member_id, user_id=user_id, organization_id=org_id, role=role
        )
    )
    db.execute(
        insert(credentials).values(
            username=key,
            membership_id=member_id,
            password_digest=password_digest(password),
        )
    )
    if phone:
        db.execute(
            insert(contacts).values(
                user_id=user_id, phone_e164=phone, verified_at=datetime.now(UTC)
            )
        )


def rotate(db: Session, username: str, password: str) -> None:
    member_id = db.scalar(
        update(credentials)
        .where(credentials.c.username == username.casefold())
        .values(password_digest=password_digest(password))
        .returning(credentials.c.membership_id)
    )
    if member_id is None:
        raise ValueError("Account ID was not found.")
    db.execute(delete(sessions).where(sessions.c.membership_id == member_id))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Provision or rotate a PeyajFlow account with database operator access."
    )
    parser.add_argument("username")
    parser.add_argument(
        "--role", choices=[role.value for role in Role], default="farmer"
    )
    parser.add_argument("--name")
    parser.add_argument("--district")
    parser.add_argument("--organization")
    parser.add_argument("--prompt-verified-phone", action="store_true")
    parser.add_argument("--replace-password", action="store_true")
    args = parser.parse_args()
    if not args.replace_password and not all(
        (args.name, args.district, args.organization)
    ):
        parser.error("Provisioning requires --name, --district and --organization.")
    password = getpass.getpass("New passphrase: ")
    if password != getpass.getpass("Repeat passphrase: "):
        raise SystemExit("Passphrases did not match.")
    engine = database_engine()
    if engine is None:
        raise SystemExit("Set DATABASE_URL first.")
    try:
        with Session(engine) as db, db.begin():
            if args.replace_password:
                rotate(db, args.username, password)
            else:
                phone = (
                    getpass.getpass("Independently verified phone (E.164): ").strip()
                    if args.prompt_verified_phone
                    else None
                )
                provision(
                    db,
                    args.username,
                    password,
                    role=Role(args.role),
                    name=args.name,
                    district=args.district,
                    organization=args.organization,
                    phone=phone,
                )
        print("Account saved.")
    except ValueError as error:
        raise SystemExit(str(error)) from None
    except IntegrityError:
        raise SystemExit(
            "The account ID or verified contact is already in use."
        ) from None
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
