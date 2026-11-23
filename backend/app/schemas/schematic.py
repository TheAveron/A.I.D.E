import re
import unicodedata
from typing import Annotated, Optional

from pydantic import AfterValidator, BaseModel, Field

from .base import MAX_DESCRIPTION_LENGTH, PartialUpdate, UTCDatetime

MAX_TITLE_LENGTH = 100
MAX_COMMENT_LENGTH = 500
MAX_TAGS = 10
MAX_TAG_LENGTH = 30

_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
# Letters (accents included), digits, spaces and hyphens
_TAG_RE = re.compile(r"^[\w\- ]+$")


def clean_title(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("The title cannot be empty")
    if len(value) > MAX_TITLE_LENGTH:
        raise ValueError(f"The title is limited to {MAX_TITLE_LENGTH} characters")
    if _CONTROL_RE.search(value):
        raise ValueError("Control characters are not allowed in the title")
    return value


def clean_description(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    if len(value) > MAX_DESCRIPTION_LENGTH:
        raise ValueError(
            f"The description is limited to {MAX_DESCRIPTION_LENGTH} characters"
        )
    return value or None


def clean_comment(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    if len(value) > MAX_COMMENT_LENGTH:
        raise ValueError(f"The comment is limited to {MAX_COMMENT_LENGTH} characters")
    return value or None


def clean_tag(value: str) -> str:
    """ "  Train  de FRET " -> "train de fret"."""
    value = unicodedata.normalize("NFC", value)
    value = re.sub(r"\s+", " ", value).strip().lower()
    if not value:
        raise ValueError("A tag cannot be empty")
    if len(value) > MAX_TAG_LENGTH:
        raise ValueError(f"A tag is limited to {MAX_TAG_LENGTH} characters")
    if not _TAG_RE.match(value) or "_" in value:
        raise ValueError("A tag only holds letters, digits, spaces and hyphens")
    return value


def clean_tags(values: list[str]) -> list[str]:
    """Cleaned, without duplicates, in the order given."""
    tags: list[str] = []
    for value in values:
        tag = clean_tag(value)
        if tag not in tags:
            tags.append(tag)
    if len(tags) > MAX_TAGS:
        raise ValueError(f"A schematic has at most {MAX_TAGS} tags")
    return tags


Title = Annotated[str, AfterValidator(clean_title)]
Tags = Annotated[list[str], AfterValidator(clean_tags)]


class SchematicUpdate(PartialUpdate):
    """What the author (or an admin) changes without uploading a file."""

    non_nullable = ("title", "tags")

    title: Optional[Title] = None
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    tags: Optional[Tags] = None


class ComplianceUpdate(BaseModel):
    compliant: bool


class VersionOut(BaseModel):
    number: int
    original_name: str
    size_bytes: int
    sha256: str
    size_x: int
    size_y: int
    size_z: int
    block_count: int
    data_version: Optional[int] = None
    comment: Optional[str] = None
    uploaded_by_user_id: Optional[int] = None
    uploaded_by_name: Optional[str] = None
    uploaded_at: UTCDatetime
    compliant: bool
    compliant_at: Optional[UTCDatetime] = None


class SchematicSummary(BaseModel):
    """A card of the gallery."""

    schematic_id: int
    title: str
    tags: list[str]
    author_user_id: Optional[int] = None
    author_name: Optional[str] = None
    has_preview: bool
    created_at: UTCDatetime
    updated_at: UTCDatetime
    version_count: int
    current: Optional[VersionOut] = None


class SchematicOut(SchematicSummary):
    description: Optional[str] = None
    versions: list[VersionOut]
    can_edit: bool  # the viewer is the author or an admin
    can_review: bool  # the viewer may grant the "compliant" badge


class TagCount(BaseModel):
    tag: str
    count: int
