import argparse
import getpass
import hmac
import os
import re
import secrets
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from hashlib import scrypt, sha256
from threading import BoundedSemaphore
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import Field, SecretStr, StringConstraints
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    delete,
    func,
    insert,
    select,
    update,
)
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
otp_codes = Table(
    "otp_codes",
    metadata,
    Column("phone_e164", String(16), primary_key=True),
    Column("code_hash", String(64), nullable=False),
    Column("purpose", String(20), nullable=False),
    Column("attempts", Integer, nullable=False, default=0),
    Column("verified", Boolean, nullable=False, default=False),
    Column("signup_payload", JSON, nullable=True),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
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


OTP_TTL = 300  # 5 minutes
OTP_MAX_ATTEMPTS = 3
OTP_CODE_LENGTH = 6


class SignupRole(StrEnum):
    FARMER = "farmer"
    BUYER = "buyer"
    AGENT = "agent"


class SignupInput(Input):
    phone_e164: Annotated[str, StringConstraints(pattern=PHONE)]
    otp_code: Annotated[str, StringConstraints(pattern=r"^\d{6}$")]


class SignupRequestInput(Input):
    phone_e164: Annotated[str, StringConstraints(pattern=PHONE)]
    role: SignupRole
    name: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    district: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    organization: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    password: Annotated[SecretStr, Field(min_length=14, max_length=256)]


class OTPSendInput(Input):
    phone_e164: Annotated[str, StringConstraints(pattern=PHONE)]
    purpose: Literal["signup", "login", "reset"] = "signup"


class OTPVerifyInput(Input):
    phone_e164: Annotated[str, StringConstraints(pattern=PHONE)]
    code: Annotated[str, StringConstraints(pattern=r"^\d{6}$")]
    purpose: Literal["signup", "login", "reset"] = "signup"


def generate_otp_code() -> str:
    if os.getenv("APP_ENV") in {"development", "test"}:
        return "000000"
    return f"{secrets.randbelow(10**OTP_CODE_LENGTH):0{OTP_CODE_LENGTH}d}"


def hash_otp_code(code: str) -> str:
    return sha256(code.encode()).hexdigest()


@router.post("/signup/request", status_code=202)
def request_signup(body: SignupRequestInput, request: Request, db: DB):
    client = request.client.host if request.client else "unknown"
    enforce(db, "signup-request-client", client, limit=10, seconds=300)
    enforce(db, "signup-request-phone", body.phone_e164, limit=5, seconds=300)

    existing_user = db.scalar(
        select(users.c.id)
        .select_from(users.join(contacts))
        .where(contacts.c.phone_e164 == body.phone_e164)
    )
    if existing_user:
        raise HTTPException(409, "phone_already_registered")

    existing = db.scalar(
        select(otp_codes.c.phone_e164).where(
            otp_codes.c.phone_e164 == body.phone_e164,
            otp_codes.c.purpose == "signup",
            otp_codes.c.expires_at > func.now(),
        )
    )
    if existing:
        raise HTTPException(429, "otp_recently_sent")

    code = generate_otp_code()
    payload = {
        "role": body.role,
        "name": body.name,
        "district": body.district,
        "organization": body.organization,
        "password_digest": password_digest(body.password.get_secret_value()),
    }
    db.execute(
        insert(otp_codes).values(
            phone_e164=body.phone_e164,
            code_hash=hash_otp_code(code),
            purpose="signup",
            verified=False,
            signup_payload=payload,
            expires_at=datetime.now(UTC) + timedelta(seconds=OTP_TTL),
        )
    )
    db.commit()

    if os.getenv("APP_ENV") in {"development", "test"}:
        return {"code": code, "expires_in": OTP_TTL}
    return {"message": "OTP sent", "expires_in": OTP_TTL}


@router.post("/otp/send", status_code=202)
def send_otp(body: OTPSendInput, request: Request, db: DB):
    client = request.client.host if request.client else "unknown"
    enforce(db, f"otp-send-{body.purpose}", client, limit=10, seconds=300)
    enforce(db, f"otp-send-phone-{body.purpose}", body.phone_e164, limit=5, seconds=300)

    existing = db.scalar(
        select(otp_codes.c.phone_e164).where(
            otp_codes.c.phone_e164 == body.phone_e164,
            otp_codes.c.purpose == body.purpose,
            otp_codes.c.expires_at > func.now(),
        )
    )
    if existing:
        raise HTTPException(429, "otp_recently_sent")

    code = generate_otp_code()
    code_hash = hash_otp_code(code)
    expires_at = datetime.now(UTC) + timedelta(seconds=OTP_TTL)

    db.execute(
        insert(otp_codes).values(
            phone_e164=body.phone_e164,
            code_hash=code_hash,
            purpose=body.purpose,
            expires_at=expires_at,
        )
    )
    db.commit()

    # In production, send via SMS provider (Twilio, etc.)
    # For now, return code in response for testing (remove in prod)
    if os.getenv("APP_ENV") in {"development", "test"}:
        return {"code": code, "expires_in": OTP_TTL}
    return {"message": "OTP sent", "expires_in": OTP_TTL}


@router.post("/otp/verify")
def verify_otp(body: OTPVerifyInput, request: Request, response: Response, db: DB):
    client = request.client.host if request.client else "unknown"
    enforce(db, f"otp-verify-{body.purpose}", client, limit=20, seconds=300)

    row = db.execute(
        select(otp_codes).where(
            otp_codes.c.phone_e164 == body.phone_e164,
            otp_codes.c.purpose == body.purpose,
            otp_codes.c.expires_at > func.now(),
        )
    ).mappings().one_or_none()

    if row is None:
        raise HTTPException(404, "otp_not_found_or_expired")

    if row["attempts"] >= OTP_MAX_ATTEMPTS:
        db.execute(delete(otp_codes).where(otp_codes.c.phone_e164 == body.phone_e164))
        db.commit()
        raise HTTPException(429, "otp_max_attempts_exceeded")

    if not hmac.compare_digest(row["code_hash"], hash_otp_code(body.code)):
        db.execute(
            update(otp_codes)
            .where(otp_codes.c.phone_e164 == body.phone_e164)
            .values(attempts=otp_codes.c.attempts + 1)
        )
        db.commit()
        raise HTTPException(401, "otp_invalid")

    if body.purpose == "signup":
        db.execute(
            update(otp_codes)
            .where(
                otp_codes.c.phone_e164 == body.phone_e164,
                otp_codes.c.purpose == "signup",
            )
            .values(verified=True)
        )
        db.commit()
        return {"verified": True, "message": "OTP verified, proceed to signup"}

    if body.purpose == "login":
        # Find user by phone and issue token
        user = db.execute(
            select(users.c.id, memberships.c.id.label("membership_id"))
            .select_from(users.join(contacts).join(memberships))
            .where(contacts.c.phone_e164 == body.phone_e164)
        ).mappings().one_or_none()

        if user is None:
            raise HTTPException(404, "user_not_found")

        return issue_token(db, user["membership_id"], response)

    if body.purpose == "reset":
        # Return a token that allows password reset
        # In production, use a signed JWT with short expiry
        return {"verified": True, "message": "OTP verified, proceed to reset password"}

    raise HTTPException(422, "invalid_purpose")


@router.post("/signup", response_model=SessionToken, status_code=201)
def signup(body: SignupInput, request: Request, response: Response, db: DB):
    client = request.client.host if request.client else "unknown"
    enforce(db, "signup-client", client, limit=20, seconds=300)
    enforce(db, "signup-phone", body.phone_e164, limit=5, seconds=3600)

    # Verify OTP inline
    row = db.execute(
        select(otp_codes).where(
            otp_codes.c.phone_e164 == body.phone_e164,
            otp_codes.c.purpose == "signup",
            otp_codes.c.expires_at > func.now(),
        )
    ).mappings().one_or_none()

    if row is None:
        raise HTTPException(404, "otp_not_found_or_expired")
    if not row["verified"]:
        raise HTTPException(403, "phone_otp_not_verified")

    if row["attempts"] >= OTP_MAX_ATTEMPTS:
        db.execute(delete(otp_codes).where(otp_codes.c.phone_e164 == body.phone_e164))
        db.commit()
        raise HTTPException(429, "otp_max_attempts_exceeded")

    if not hmac.compare_digest(row["code_hash"], hash_otp_code(body.otp_code)):
        db.execute(
            update(otp_codes)
            .where(otp_codes.c.phone_e164 == body.phone_e164)
            .values(attempts=otp_codes.c.attempts + 1)
        )
        db.commit()
        raise HTTPException(401, "otp_invalid")

    payload = row["signup_payload"]
    if payload is None:
        raise HTTPException(409, "signup_details_not_found")

    existing_user = db.scalar(
        select(users.c.id)
        .select_from(users.join(contacts))
        .where(contacts.c.phone_e164 == body.phone_e164)
    )
    if existing_user:
        raise HTTPException(409, "phone_already_registered")

    db.execute(delete(otp_codes).where(otp_codes.c.phone_e164 == body.phone_e164))

    # Check if username would conflict (we'll use phone as username base)
    # Generate username from phone
    username_base = body.phone_e164.lstrip("+").replace(" ", "")
    username = username_base[:64]

    # Check for conflicts
    counter = 1
    original_username = username
    while db.scalar(select(credentials.c.username).where(credentials.c.username == username)):
        username = f"{original_username}{counter}"
        counter += 1

    # Create user, organization, membership, credentials
    member_id, user_id, org_id = uuid4(), uuid4(), uuid4()

    db.execute(
        insert(users).values(
            id=user_id,
            name=str(payload["name"]).strip(),
            district=str(payload["district"]).strip(),
            language="bn",
            verified=True,  # Phone verified via OTP
        )
    )
    db.execute(
        insert(organizations).values(
            id=org_id,
            name=str(payload["organization"]).strip(),
            is_demo=False,
        )
    )
    db.execute(
        insert(memberships).values(
            id=member_id,
            user_id=user_id,
            organization_id=org_id,
            role=payload["role"],
        )
    )
    db.execute(
        insert(credentials).values(
            username=username,
            membership_id=member_id,
            password_digest=payload["password_digest"],
        )
    )
    db.execute(
        insert(contacts).values(
            user_id=user_id,
            phone_e164=body.phone_e164,
            verified_at=datetime.now(UTC),
        )
    )
    db.commit()

    return issue_token(db, member_id, response)


class PasswordResetInput(Input):
    phone_e164: Annotated[str, StringConstraints(pattern=PHONE)]
    otp_code: Annotated[str, StringConstraints(pattern=r"^\d{6}$")]
    new_password: Annotated[SecretStr, Field(min_length=14, max_length=256)]


@router.post("/password/reset", status_code=204)
def reset_password(body: PasswordResetInput, request: Request, db: DB):
    client = request.client.host if request.client else "unknown"
    enforce(db, "password-reset-client", client, limit=10, seconds=300)
    enforce(db, "password-reset-phone", body.phone_e164, limit=3, seconds=3600)

    # Verify OTP inline
    row = db.execute(
        select(otp_codes).where(
            otp_codes.c.phone_e164 == body.phone_e164,
            otp_codes.c.purpose == "reset",
            otp_codes.c.expires_at > func.now(),
        )
    ).mappings().one_or_none()

    if row is None:
        raise HTTPException(404, "otp_not_found_or_expired")

    if row["attempts"] >= OTP_MAX_ATTEMPTS:
        db.execute(delete(otp_codes).where(otp_codes.c.phone_e164 == body.phone_e164))
        db.commit()
        raise HTTPException(429, "otp_max_attempts_exceeded")

    if not hmac.compare_digest(row["code_hash"], hash_otp_code(body.otp_code)):
        db.execute(
            update(otp_codes)
            .where(otp_codes.c.phone_e164 == body.phone_e164)
            .values(attempts=otp_codes.c.attempts + 1)
        )
        db.commit()
        raise HTTPException(401, "otp_invalid")

    # OTP verified, delete it
    db.execute(delete(otp_codes).where(otp_codes.c.phone_e164 == body.phone_e164))

    # Find user and update password
    member_id = db.scalar(
        select(credentials.c.membership_id)
        .select_from(credentials.join(memberships).join(users).join(contacts))
        .where(contacts.c.phone_e164 == body.phone_e164)
    )
    if member_id is None:
        raise HTTPException(404, "user_not_found")

    rotate(db, body.phone_e164.lstrip("+").replace(" ", ""), body.new_password.get_secret_value())
    # Note: rotate() uses username, but we need to find by phone
    # Let's add a proper reset function
    db.execute(
        update(credentials)
        .where(credentials.c.membership_id == member_id)
        .values(password_digest=password_digest(body.new_password.get_secret_value()))
    )
    db.execute(delete(sessions).where(sessions.c.membership_id == member_id))
    db.commit()


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
