import logging
from datetime import date, datetime
from decimal import Decimal
from hashlib import sha256
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field, ValidationError, field_validator
from sqlalchemy import (
    JSON,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Uuid,
    func,
    insert,
    select,
)
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.auth import Actor, Input, Role, audit, require_role
from app.condition import MAX_PHOTO_BYTES, QUALITY_VERSION, VisibleFlag, prepare_photo
from app.database import DB, metadata
from app.lots import NonnegativeKg, get_lot, today
from app.photo_storage import PhotoStorage

router = APIRouter(prefix="/v1/lots/{lot_id}", tags=["Inspection and condition"])
logger = logging.getLogger(__name__)
UPLOAD_REQUEST_BYTES = 13 * 1024 * 1024


class InspectionUploadLimit:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope["method"] != "POST"
            or not scope["path"].rstrip("/").endswith("/inspections")
        ):
            await self.app(scope, receive, send)
            return
        content_length = dict(scope["headers"]).get(b"content-length", b"0")
        if content_length.isdigit() and int(content_length) > UPLOAD_REQUEST_BYTES:
            await JSONResponse({"detail": "image_too_large"}, status_code=413)(
                scope, receive, send
            )
            return
        received = 0

        async def bounded_receive():
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > UPLOAD_REQUEST_BYTES:
                raise HTTPException(413, "image_too_large")
            return message

        await self.app(scope, bounded_receive, send)


inspections = Table(
    "inspections",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid4),
    Column("lot_id", ForeignKey("lots.id"), nullable=False, index=True),
    Column("actor_id", ForeignKey("memberships.id"), nullable=False),
    Column("observed_on", Date, nullable=False),
    Column("curing", String(10), nullable=False),
    Column("ventilation", String(10), nullable=False),
    Column("moisture", String(10), nullable=False),
    Column("odor", String(10), nullable=False),
    Column("temperature_c", Numeric(4, 1)),
    Column("humidity_pct", Numeric(4, 1)),
    Column("sample_kg", Numeric(12, 3)),
    Column("visible_flags", JSON, nullable=False),
    Column("notes", String(500), nullable=False),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
)
photos = Table(
    "inspection_photos",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid4),
    Column("inspection_id", ForeignKey("inspections.id"), nullable=False, index=True),
    Column("storage_key", String(48), nullable=False, unique=True),
    Column("width", Integer, nullable=False),
    Column("height", Integer, nullable=False),
    Column("bytes", Integer, nullable=False),
    Column("sha256", String(64), nullable=False),
    Column("quality_flags", JSON, nullable=False),
    Column("quality_version", String(24), nullable=False),
)
reviews = Table(
    "inspection_reviews",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid4),
    Column("inspection_id", ForeignKey("inspections.id"), nullable=False, index=True),
    Column("actor_id", ForeignKey("memberships.id"), nullable=False),
    Column("source", String(20), nullable=False),
    Column("flags", JSON, nullable=False),
    Column("reason", String(500), nullable=False),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
)


def validate_flags(flags: list[VisibleFlag]) -> list[VisibleFlag]:
    if not flags or len(set(flags)) != len(flags):
        raise ValueError("Select one or more distinct visible flags")
    if len(flags) > 1 and (
        VisibleFlag.NO_OBVIOUS_DEFECT in flags or VisibleFlag.UNCERTAIN in flags
    ):
        raise ValueError("An uncertain or clear observation must stand alone")
    return flags


class Observations(Input):
    observed_on: date
    curing: Literal["cured", "uncured", "unknown"]
    ventilation: Literal["good", "poor", "unknown"]
    moisture: Literal["dry", "wet", "unknown"]
    odor: Literal["normal", "off", "unknown"]
    temperature_c: Annotated[Decimal, Field(ge=-20, le=65, decimal_places=1)] | None = (
        None
    )
    humidity_pct: Annotated[Decimal, Field(ge=0, le=100, decimal_places=1)] | None = (
        None
    )
    sample_kg: NonnegativeKg | None = None
    visible_flags: Annotated[list[VisibleFlag], Field(max_length=5)]
    notes: Annotated[str, Field(max_length=500)] = ""

    @field_validator("visible_flags")
    @classmethod
    def flags_valid(cls, value):
        return validate_flags(value)


class ReviewInput(Input):
    flags: Annotated[list[VisibleFlag], Field(max_length=5)]
    reason: Annotated[str, Field(min_length=1, max_length=500)]

    @field_validator("flags")
    @classmethod
    def flags_valid(cls, value):
        return validate_flags(value)


class PhotoView(BaseModel):
    id: UUID
    width: int
    height: int
    quality_flags: list[str]
    quality_version: str


class ReviewView(BaseModel):
    source: Literal["owner_correction", "human_review"]
    flags: list[VisibleFlag]
    reason: str
    created_at: datetime


class InspectionView(Observations):
    id: UUID
    created_at: datetime
    photos: list[PhotoView]
    quality_assessment: Literal["uncertain_or_low_quality", "needs_human_review"]
    confidence: None = None
    effective_flags: list[VisibleFlag]
    provenance: Literal["submitted_observation", "owner_correction", "human_review"]
    review_history: list[ReviewView]


def review_rows(db: Session, inspection_id: UUID) -> list[RowMapping]:
    return list(
        db.execute(
            select(reviews)
            .where(reviews.c.inspection_id == inspection_id)
            .order_by(reviews.c.created_at.desc(), reviews.c.id)
            .limit(20)
        ).mappings()
    )


def inspection_view(db: Session, row: RowMapping) -> InspectionView:
    images = [
        PhotoView.model_validate(item)
        for item in db.execute(
            select(photos)
            .where(photos.c.inspection_id == row["id"])
            .order_by(photos.c.id)
        ).mappings()
    ]
    history = [ReviewView.model_validate(item) for item in review_rows(db, row["id"])]
    values = {
        name: row[name] for name in (*Observations.model_fields, "id", "created_at")
    }
    return InspectionView(
        **values,
        photos=images,
        quality_assessment="needs_human_review"
        if any(not image.quality_flags for image in images)
        else "uncertain_or_low_quality",
        effective_flags=history[0].flags if history else row["visible_flags"],
        provenance=history[0].source if history else "submitted_observation",
        review_history=history,
    )


def observations_query(lot_id: UUID):
    return (
        select(inspections)
        .where(inspections.c.lot_id == lot_id)
        .order_by(
            inspections.c.observed_on.desc(),
            inspections.c.created_at.desc(),
            inspections.c.id,
        )
    )


@router.get("/inspections", response_model=list[InspectionView])
def list_inspections(lot_id: UUID, actor: Actor, db: DB):
    get_lot(db, actor, lot_id)
    return [
        inspection_view(db, row)
        for row in db.execute(observations_query(lot_id).limit(20)).mappings()
    ]


@router.post("/inspections", response_model=InspectionView, status_code=201)
def create_inspection(
    lot_id: UUID,
    actor: Actor,
    db: DB,
    observations: Annotated[str, Form(max_length=4096)],
    images: Annotated[list[UploadFile], File()],
    consent: Annotated[bool, Form()],
):
    require_role(actor, Role.FARMER, Role.AGENT)
    lot = get_lot(db, actor, lot_id)
    try:
        body = Observations.model_validate_json(observations)
    except ValidationError as error:
        raise HTTPException(422, "invalid_input") from error
    if not lot["stored_on"] <= body.observed_on <= today():
        raise HTTPException(422, "inspection_date_invalid")
    if not 2 <= len(images) <= 4:
        raise HTTPException(422, "photos_required")
    if not consent:
        raise HTTPException(422, "confirmation_required")
    files = [
        prepare_photo(image.file.read(MAX_PHOTO_BYTES + 1), image.content_type)
        for image in images
    ]
    storage = PhotoStorage()
    row = (
        db.execute(
            insert(inspections)
            .values(
                **body.model_dump(),
                lot_id=lot_id,
                actor_id=actor.membership_id,
            )
            .returning(inspections)
        )
        .mappings()
        .one()
    )
    uploaded = []
    try:
        for image in files:
            key = f"{uuid4().hex}.jpg"
            uploaded.append(key)
            storage.put(key, image.content)
            db.execute(
                insert(photos).values(
                    inspection_id=row["id"],
                    storage_key=key,
                    width=image.width,
                    height=image.height,
                    bytes=len(image.content),
                    sha256=sha256(image.content).hexdigest(),
                    quality_flags=image.quality_flags,
                    quality_version=QUALITY_VERSION,
                )
            )
        audit(
            db,
            actor,
            "inspection.submitted",
            row["id"],
            lot_id=str(lot_id),
            photo_consent="yes",
        )
        view = inspection_view(db, row)
    except Exception:
        for key in uploaded:
            try:
                storage.remove(key)
            except Exception:
                logger.warning("Could not remove an incomplete inspection object")
        raise
    db.commit()
    return view


@router.get(
    "/inspection-photos/{photo_id}", responses={200: {"content": {"image/jpeg": {}}}}
)
def read_photo(lot_id: UUID, photo_id: UUID, actor: Actor, db: DB):
    get_lot(db, actor, lot_id)
    key = db.scalar(
        select(photos.c.storage_key)
        .select_from(photos.join(inspections))
        .where(
            photos.c.id == photo_id,
            inspections.c.lot_id == lot_id,
        )
    )
    if key is None:
        raise HTTPException(404, "not_found")
    return Response(
        PhotoStorage().get(key),
        media_type="image/jpeg",
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/inspections/{inspection_id}/review", response_model=InspectionView)
def review_inspection(
    lot_id: UUID, inspection_id: UUID, body: ReviewInput, actor: Actor, db: DB
):
    get_lot(db, actor, lot_id)
    row = (
        db.execute(
            select(inspections)
            .where(inspections.c.id == inspection_id, inspections.c.lot_id == lot_id)
            .with_for_update()
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise HTTPException(404, "not_found")
    source = "human_review"
    if actor.role == Role.FARMER:
        if any(
            review["source"] == "human_review"
            for review in review_rows(db, inspection_id)
        ):
            raise HTTPException(409, "review_locked")
        source = "owner_correction"
    db.execute(
        insert(reviews).values(
            inspection_id=inspection_id,
            actor_id=actor.membership_id,
            source=source,
            flags=body.flags,
            reason=body.reason,
        )
    )
    audit(db, actor, "inspection.reviewed", inspection_id, source=source)
    db.commit()
    return inspection_view(db, row)
