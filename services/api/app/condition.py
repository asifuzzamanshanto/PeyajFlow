from dataclasses import dataclass
from enum import StrEnum
from io import BytesIO

from fastapi import HTTPException
from PIL import Image, ImageFilter, ImageOps, ImageStat, UnidentifiedImageError

MAX_PHOTO_BYTES = 3 * 1024 * 1024
MAX_PIXELS = 12_000_000
QUALITY_VERSION = "photo-quality-v1"
SUPPORTED = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}


class VisibleFlag(StrEnum):
    NO_OBVIOUS_DEFECT = "no_obvious_defect"
    ROT_OR_MOLD = "visible_rot_or_mold"
    SPROUTING = "sprouting"
    DAMAGE = "physical_damage"
    UNCERTAIN = "uncertain_or_low_quality"


@dataclass(frozen=True)
class Photo:
    content: bytes
    width: int
    height: int
    quality_flags: list[str]


def quality_flags(image: Image.Image) -> list[str]:
    flags = []
    if min(image.size) < 320:
        flags.append("small_image")
    gray = image.convert("L")
    gray.thumbnail((480, 480))
    mean = ImageStat.Stat(gray).mean[0]
    if mean < 45:
        flags.append("too_dark")
    if mean > 220:
        flags.append("too_bright")
    if min(gray.size) > 8:
        edges = gray.filter(ImageFilter.FIND_EDGES).crop(
            (3, 3, gray.width - 3, gray.height - 3)
        )
        if ImageStat.Stat(edges).var[0] < 18:
            flags.append("low_detail")
    return flags


def prepare_photo(data: bytes, content_type: str | None) -> Photo:
    if len(data) > MAX_PHOTO_BYTES:
        raise HTTPException(413, "image_too_large")
    expected = SUPPORTED.get(content_type or "")
    if not expected:
        raise HTTPException(415, "image_invalid")
    try:
        with Image.open(BytesIO(data)) as original:
            if original.format != expected or getattr(original, "is_animated", False):
                raise HTTPException(415, "image_invalid")
            if original.width * original.height > MAX_PIXELS:
                raise HTTPException(413, "image_too_large")
            original.load()
            image = ImageOps.exif_transpose(original).convert("RGB")
            flags = quality_flags(image)
            image.thumbnail((1400, 1400))
            clean = Image.new("RGB", image.size)
            clean.paste(image)
            output = BytesIO()
            clean.save(output, "JPEG", quality=85, optimize=True)
            return Photo(output.getvalue(), clean.width, clean.height, flags)
    except Image.DecompressionBombError as error:
        raise HTTPException(413, "image_too_large") from error
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as error:
        raise HTTPException(415, "image_invalid") from error
