"""The schematics gallery: structure files (.nbt) shared by the players.

Everything here needs an account: reading the gallery as well as downloading.
Any account uploads; the author (or an admin) changes and deletes; train
admins (and admins) say whether a version complies with the railway standards.
"""

from typing import Annotated, Optional

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Query,
                     UploadFile, status)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import audit
from ..crud import schematic as crud
from ..database import User, get_db
from ..schemas import (ComplianceUpdate, SchematicOut, SchematicSummary,
                       SchematicUpdate, TagCount)
from ..schemas.schematic import MAX_TITLE_LENGTH, clean_tag

router = APIRouter(prefix="/schematics", tags=["Schematics"])

_FILE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Cache-Control": "private, max-age=300",
}


def _split_tags(raw: Optional[str]) -> list[str]:
    """Tags sent by a form: "train, fret,  gare" (empty parts are ignored)."""
    return [part for part in (raw or "").split(",") if part.strip()]


async def _preview(upload: Optional[UploadFile]) -> Optional[tuple[bytes, str, str]]:
    """The checked preview of a form, or None when no file was chosen."""
    if upload is None or not upload.filename:
        return None
    data = await crud.read_upload(upload, crud.MAX_PREVIEW_BYTES, "preview image")
    if not data:
        return None
    ext, media_type = crud.check_image(data)
    return data, ext, media_type


@router.get("", response_model=list[SchematicSummary])
def list_schematics(
    tag: Annotated[list[str], Query(max_length=10)] = [],
    q: Optional[str] = Query(None, max_length=MAX_TITLE_LENGTH),
    author_user_id: Optional[int] = None,
    compliant: Optional[bool] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 60,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        tags = [clean_tag(t) for t in tag]
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    schematics = crud.list_schematics(
        db,
        tags=tags,
        search=(q or "").strip() or None,
        author_user_id=author_user_id,
        compliant=compliant,
        skip=skip,
        limit=limit,
    )
    return [crud.summary(s) for s in schematics]


@router.get("/tags", response_model=list[TagCount])
def list_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return [TagCount(tag=tag, count=n) for tag, n in crud.tag_counts(db)]


@router.get("/{schematic_id}", response_model=SchematicOut)
def read_schematic(
    schematic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.detail(crud.get_schematic(db, schematic_id), current_user)


@router.post("", response_model=SchematicOut, status_code=status.HTTP_201_CREATED)
async def create_schematic(
    title: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    description: Annotated[Optional[str], Form()] = None,
    tags: Annotated[Optional[str], Form()] = None,
    preview: Annotated[Optional[UploadFile], File()] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await crud.read_upload(file, crud.MAX_NBT_BYTES, "schematic")
    schematic = crud.create_schematic(
        db,
        current_user,
        title=title,
        description=description,
        tags=_split_tags(tags),
        data=data,
        filename=file.filename,
        preview=await _preview(preview),
    )
    return crud.detail(schematic, current_user)


@router.put("/{schematic_id}", response_model=SchematicOut)
def update_schematic(
    schematic_id: int,
    body: SchematicUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    schematic = crud.get_schematic(db, schematic_id)
    crud.check_can_edit(current_user, schematic)
    if crud.is_override(current_user, schematic):
        audit.record(
            db,
            current_user,
            audit.AuditAction.SCHEMATIC_CHANGED,
            "schematic",
            schematic.schematic_id,
            schematic.title,
        )
    schematic = crud.update_schematic(
        db,
        schematic,
        title=body.title,
        description=body.description,
        description_set="description" in body.model_fields_set,
        tags=body.tags,
    )
    return crud.detail(schematic, current_user)


@router.post(
    "/{schematic_id}/versions",
    response_model=SchematicOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_version(
    schematic_id: int,
    file: Annotated[UploadFile, File()],
    comment: Annotated[Optional[str], Form()] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """A new file for a schematic; the earlier ones stay downloadable."""
    schematic = crud.get_schematic(db, schematic_id)
    crud.check_can_edit(current_user, schematic)
    data = await crud.read_upload(file, crud.MAX_NBT_BYTES, "schematic")
    if crud.is_override(current_user, schematic):
        audit.record(
            db,
            current_user,
            audit.AuditAction.SCHEMATIC_CHANGED,
            "schematic",
            schematic.schematic_id,
            schematic.title,
            "new version",
        )
    crud.add_version(
        db, current_user, schematic, data=data, filename=file.filename, comment=comment
    )
    return crud.detail(schematic, current_user)


@router.put("/{schematic_id}/preview", response_model=SchematicOut)
async def replace_preview(
    schematic_id: int,
    preview: Annotated[UploadFile, File()],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    schematic = crud.get_schematic(db, schematic_id)
    crud.check_can_edit(current_user, schematic)
    image = await _preview(preview)
    if image is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No image was sent")
    return crud.detail(crud.set_preview(db, schematic, image), current_user)


@router.delete("/{schematic_id}/preview", response_model=SchematicOut)
def delete_preview(
    schematic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    schematic = crud.get_schematic(db, schematic_id)
    crud.check_can_edit(current_user, schematic)
    return crud.detail(crud.set_preview(db, schematic, None), current_user)


@router.get("/{schematic_id}/preview")
def read_preview(
    schematic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    schematic = crud.get_schematic(db, schematic_id)
    if not schematic.preview_file:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This schematic has no preview")
    path = crud.stored_path(schematic.preview_file)
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "The preview file is missing")
    return FileResponse(path, media_type=schematic.preview_type, headers=_FILE_HEADERS)


@router.get("/{schematic_id}/versions/{number}/download")
def download_version(
    schematic_id: int,
    number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    schematic = crud.get_schematic(db, schematic_id)
    version = crud.get_version(schematic, number)
    path = crud.stored_path(version.file_name)
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "The file is missing")
    return FileResponse(
        path,
        media_type="application/octet-stream",
        filename=crud.download_name(schematic, version),
        headers=_FILE_HEADERS,
    )


@router.put("/{schematic_id}/versions/{number}/compliance", response_model=SchematicOut)
def set_compliance(
    schematic_id: int,
    number: int,
    body: ComplianceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Say whether a version complies with the railway standards."""
    if not crud.can_review(current_user):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Only a train admin (or an admin) can review a schematic",
        )
    schematic = crud.get_schematic(db, schematic_id)
    version = crud.get_version(schematic, number)
    if version.compliant != body.compliant:
        crud.set_compliant(db, current_user, version, body.compliant)
        audit.record(
            db,
            current_user,
            audit.AuditAction.SCHEMATIC_COMPLIANCE,
            "schematic",
            schematic.schematic_id,
            schematic.title,
            f"v{version.number}: {'compliant' if body.compliant else 'not compliant'}",
        )
        db.commit()
        db.refresh(schematic)
    return crud.detail(schematic, current_user)


@router.delete("/{schematic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schematic(
    schematic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a schematic with all its versions and files."""
    schematic = crud.get_schematic(db, schematic_id)
    crud.check_can_edit(current_user, schematic)
    if crud.is_override(current_user, schematic):
        audit.record(
            db,
            current_user,
            audit.AuditAction.SCHEMATIC_DELETED,
            "schematic",
            schematic.schematic_id,
            schematic.title,
        )
    crud.delete_schematic(db, schematic)
    return None
