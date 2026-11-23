"""The schematics gallery: files on disk, records in the database.

Files are stored under STORAGE_DIR with a random name ("<32 hex>.nbt",
"<32 hex>.png"): the name a player gave is only kept for display, so it can
never be used to reach another path. A file is written before the database
commit and removed again if the commit fails; after a deletion, the files go
once the commit has succeeded.
"""

import hashlib
import logging
import os
import re
import secrets
from pathlib import Path
from typing import Iterable, Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.nbt import NbtError, StructureInfo, read_structure
from ..core.settings import SCHEMATICS_DIR
from ..database import (GlobalRoleName, Schematic, SchematicTag,
                        SchematicVersion, User)
from ..database.clock import utcnow
from ..schemas.schematic import (SchematicOut, SchematicSummary, VersionOut,
                                 clean_comment, clean_description, clean_tags,
                                 clean_title)

logger = logging.getLogger("aide")

STORAGE_DIR: Path = SCHEMATICS_DIR
MAX_NBT_BYTES = 5 * 1024 * 1024
MAX_PREVIEW_BYTES = 2 * 1024 * 1024
MAX_VERSIONS = 100
_CHUNK = 64 * 1024
_STORED_NAME = re.compile(r"^[0-9a-f]{32}\.(nbt|png|jpg|webp)$")

# (magic bytes test, extension, media type)
_IMAGE_TYPES = (
    (lambda b: b.startswith(b"\x89PNG\r\n\x1a\n"), ".png", "image/png"),
    (lambda b: b.startswith(b"\xff\xd8\xff"), ".jpg", "image/jpeg"),
    (lambda b: b[:4] == b"RIFF" and b[8:12] == b"WEBP", ".webp", "image/webp"),
)


def _error(code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=code, detail=detail)


def _valid(clean, value):
    """`clean(value)`, its ValueError turned into a 422 for the user."""
    try:
        return clean(value)
    except ValueError as e:
        raise _error(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))


# ------------------------------------------------------------- permissions


def can_edit(user: User, schematic: Schematic) -> bool:
    """The author, or an admin."""
    return user.is_admin or (
        schematic.author_user_id is not None
        and schematic.author_user_id == user.user_id
    )


def is_override(user: User, schematic: Schematic) -> bool:
    """An admin acting on a schematic that is not theirs (audited)."""
    return user.is_admin and schematic.author_user_id != user.user_id


def can_review(user: User) -> bool:
    """Who may say a schematic complies with the railway standards."""
    return user.is_admin or user.has_global_role(GlobalRoleName.TRAIN_ADMIN.value)


def check_can_edit(user: User, schematic: Schematic) -> None:
    if not can_edit(user, schematic):
        raise _error(
            status.HTTP_403_FORBIDDEN,
            "Only the author (or an admin) can change this schematic",
        )


# ------------------------------------------------------------------ files


async def read_upload(upload: UploadFile, limit: int, what: str) -> bytes:
    """The whole upload, refused (413) as soon as it goes over `limit`."""
    chunks, total = [], 0
    while True:
        chunk = await upload.read(_CHUNK)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise _error(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                f"The {what} is limited to {limit // (1024 * 1024)} MB",
            )
        chunks.append(chunk)
    return b"".join(chunks)


def original_name(filename: Optional[str]) -> str:
    """The name the player gave, without any directory, for display only."""
    name = re.split(r"[\\/]", filename or "")[-1].strip()
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)
    return name[:255] or "schematic.nbt"


def check_structure(filename: Optional[str], data: bytes) -> StructureInfo:
    """A .nbt name and a readable structure inside, or 400."""
    if not (filename or "").lower().endswith(".nbt"):
        raise _error(status.HTTP_400_BAD_REQUEST, "Only .nbt files are accepted")
    try:
        return read_structure(data)
    except NbtError as e:
        raise _error(status.HTTP_400_BAD_REQUEST, str(e))


def check_image(data: bytes) -> tuple[str, str]:
    """(extension, media type) of a PNG, JPEG or WebP image, or 400."""
    for test, ext, media_type in _IMAGE_TYPES:
        if test(data[:16]):
            return ext, media_type
    raise _error(
        status.HTTP_400_BAD_REQUEST, "The preview must be a PNG, JPEG or WebP image"
    )


def stored_path(name: str) -> Path:
    """The path of a stored file. Only names this module made are accepted."""
    if not _STORED_NAME.match(name):
        raise ValueError(f"Unexpected stored file name: {name!r}")
    return STORAGE_DIR / name


def _store(data: bytes, ext: str) -> str:
    """Write `data` under a new random name; returns that name."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    name = secrets.token_hex(16) + ext
    path = stored_path(name)
    tmp = path.with_name(f".{name}.tmp")
    try:
        tmp.write_bytes(data)
        os.replace(tmp, path)
    except OSError:
        tmp.unlink(missing_ok=True)
        logger.exception("Could not store a schematic file")
        raise _error(status.HTTP_500_INTERNAL_SERVER_ERROR, "Could not store the file")
    return name


def _remove(names: Iterable[Optional[str]]) -> None:
    for name in names:
        if not name:
            continue
        try:
            stored_path(name).unlink(missing_ok=True)
        except (OSError, ValueError):
            logger.exception("Could not remove the schematic file %s", name)


def _commit(db: Session, written: list[str]) -> None:
    """Commit, or roll back and remove the files written for this change."""
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        _remove(written)
        raise _error(
            status.HTTP_409_CONFLICT,
            "Somebody changed this schematic at the same time, try again",
        )
    except Exception:
        db.rollback()
        _remove(written)
        raise


# ------------------------------------------------------------------ reads


def get_schematic(db: Session, schematic_id: int) -> Schematic:
    schematic = db.get(Schematic, schematic_id)
    if schematic is None:
        raise _error(status.HTTP_404_NOT_FOUND, "Schematic not found")
    return schematic


def get_version(schematic: Schematic, number: int) -> SchematicVersion:
    for version in schematic.versions:
        if version.number == number:
            return version
    raise _error(status.HTTP_404_NOT_FOUND, "Version not found")


def list_schematics(
    db: Session,
    *,
    tags: list[str],
    search: Optional[str],
    author_user_id: Optional[int],
    compliant: Optional[bool],
    skip: int,
    limit: int,
) -> list[Schematic]:
    query = db.query(Schematic)
    for tag in tags:  # every tag asked for
        query = query.filter(Schematic.tags.any(SchematicTag.tag == tag))
    if search:
        pattern = (
            "%"
            + search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            + "%"
        )
        query = query.filter(Schematic.title.ilike(pattern, escape="\\"))
    if author_user_id is not None:
        query = query.filter(Schematic.author_user_id == author_user_id)
    if compliant is not None:
        latest = (
            db.query(func.max(SchematicVersion.number))
            .filter(SchematicVersion.schematic_id == Schematic.schematic_id)
            .correlate(Schematic)
            .scalar_subquery()
        )
        current_compliant = Schematic.versions.any(
            (SchematicVersion.number == latest) & SchematicVersion.compliant.is_(True)
        )
        query = query.filter(current_compliant if compliant else ~current_compliant)
    return (
        query.order_by(Schematic.updated_at.desc(), Schematic.schematic_id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def tag_counts(db: Session, limit: int = 200) -> list[tuple[str, int]]:
    """The tags in use, the most used first (suggestions for the forms)."""
    count = func.count(SchematicTag.schematic_id)
    rows = (
        db.query(SchematicTag.tag, count)
        .group_by(SchematicTag.tag)
        .order_by(count.desc(), SchematicTag.tag)
        .limit(limit)
        .all()
    )
    return [(tag, n) for tag, n in rows]


# ----------------------------------------------------------------- writes


def _new_version(
    schematic: Schematic,
    user: User,
    number: int,
    data: bytes,
    filename: Optional[str],
    info: StructureInfo,
    comment: Optional[str],
    written: list[str],
) -> SchematicVersion:
    stored = _store(data, ".nbt")
    written.append(stored)
    return SchematicVersion(
        schematic=schematic,
        number=number,
        file_name=stored,
        original_name=original_name(filename),
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        size_x=info.size_x,
        size_y=info.size_y,
        size_z=info.size_z,
        block_count=info.block_count,
        data_version=info.data_version,
        comment=comment,
        uploaded_by_user_id=user.user_id,
    )


def _set_tags(schematic: Schematic, tags: list[str]) -> None:
    current = {t.tag: t for t in schematic.tags}
    schematic.tags = [current.get(tag) or SchematicTag(tag=tag) for tag in tags]


def create_schematic(
    db: Session,
    user: User,
    *,
    title: str,
    description: Optional[str],
    tags: list[str],
    data: bytes,
    filename: Optional[str],
    preview: Optional[tuple[bytes, str, str]],
) -> Schematic:
    """`preview`: (bytes, extension, media type), already checked."""
    info = check_structure(filename, data)
    schematic = Schematic(
        title=_valid(clean_title, title),
        description=_valid(clean_description, description),
        author_user_id=user.user_id,
    )
    _set_tags(schematic, _valid(clean_tags, tags))
    written: list[str] = []
    try:
        _new_version(schematic, user, 1, data, filename, info, None, written)
        if preview:
            schematic.preview_file = _store(preview[0], preview[1])
            schematic.preview_type = preview[2]
            written.append(schematic.preview_file)
        db.add(schematic)
    except Exception:
        _remove(written)
        raise
    _commit(db, written)
    db.refresh(schematic)
    return schematic


def add_version(
    db: Session,
    user: User,
    schematic: Schematic,
    *,
    data: bytes,
    filename: Optional[str],
    comment: Optional[str],
) -> SchematicVersion:
    info = check_structure(filename, data)
    if len(schematic.versions) >= MAX_VERSIONS:
        raise _error(
            status.HTTP_400_BAD_REQUEST,
            f"A schematic has at most {MAX_VERSIONS} versions",
        )
    number = max((v.number for v in schematic.versions), default=0) + 1
    written: list[str] = []
    version = _new_version(
        schematic,
        user,
        number,
        data,
        filename,
        info,
        _valid(clean_comment, comment),
        written,
    )
    db.add(version)
    schematic.updated_at = utcnow()
    _commit(db, written)
    db.refresh(schematic)
    return version


def update_schematic(
    db: Session,
    schematic: Schematic,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    description_set: bool = False,
    tags: Optional[list[str]] = None,
) -> Schematic:
    if title is not None:
        schematic.title = _valid(clean_title, title)
    if description_set:
        schematic.description = _valid(clean_description, description)
    if tags is not None:
        _set_tags(schematic, _valid(clean_tags, tags))
    schematic.updated_at = utcnow()
    _commit(db, [])
    db.refresh(schematic)
    return schematic


def set_preview(
    db: Session, schematic: Schematic, preview: Optional[tuple[bytes, str, str]]
) -> Schematic:
    """Replace (or, with None, remove) the preview image."""
    old = schematic.preview_file
    written: list[str] = []
    if preview:
        schematic.preview_file = _store(preview[0], preview[1])
        schematic.preview_type = preview[2]
        written.append(schematic.preview_file)
    else:
        schematic.preview_file = None
        schematic.preview_type = None
    _commit(db, written)
    _remove([old])
    db.refresh(schematic)
    return schematic


def set_compliant(
    db: Session, user: User, version: SchematicVersion, compliant: bool
) -> SchematicVersion:
    version.compliant = compliant
    version.compliant_by_user_id = user.user_id if compliant else None
    version.compliant_at = utcnow() if compliant else None
    return version


def delete_schematic(db: Session, schematic: Schematic) -> None:
    files = [v.file_name for v in schematic.versions] + [schematic.preview_file]
    db.delete(schematic)
    _commit(db, [])
    _remove(files)


# ---------------------------------------------------------------- outputs


def version_out(version: SchematicVersion) -> VersionOut:
    return VersionOut(
        number=version.number,
        original_name=version.original_name,
        size_bytes=version.size_bytes,
        sha256=version.sha256,
        size_x=version.size_x,
        size_y=version.size_y,
        size_z=version.size_z,
        block_count=version.block_count,
        data_version=version.data_version,
        comment=version.comment,
        uploaded_by_user_id=version.uploaded_by_user_id,
        uploaded_by_name=version.uploaded_by.username if version.uploaded_by else None,
        uploaded_at=version.uploaded_at,
        compliant=version.compliant,
        compliant_at=version.compliant_at,
    )


def _summary_fields(schematic: Schematic) -> dict:
    current = schematic.current_version
    return dict(
        schematic_id=schematic.schematic_id,
        title=schematic.title,
        tags=schematic.tag_names,
        author_user_id=schematic.author_user_id,
        author_name=schematic.author.username if schematic.author else None,
        has_preview=schematic.preview_file is not None,
        created_at=schematic.created_at,
        updated_at=schematic.updated_at,
        version_count=len(schematic.versions),
        current=version_out(current) if current else None,
    )


def summary(schematic: Schematic) -> SchematicSummary:
    return SchematicSummary(**_summary_fields(schematic))


def detail(schematic: Schematic, viewer: User) -> SchematicOut:
    return SchematicOut(
        **_summary_fields(schematic),
        description=schematic.description,
        versions=[version_out(v) for v in reversed(schematic.versions)],
        can_edit=can_edit(viewer, schematic),
        can_review=can_review(viewer),
    )


def download_name(schematic: Schematic, version: SchematicVersion) -> str:
    """'Gare de passage' v2 -> "Gare_de_passage-v2.nbt"."""
    base = re.sub(r"[^\w\-]+", "_", schematic.title, flags=re.UNICODE).strip("_")
    return f"{(base or 'schematic')[:80]}-v{version.number}.nbt"
