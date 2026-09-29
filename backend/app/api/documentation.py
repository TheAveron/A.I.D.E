import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..core import get_current_user
from ..crud import normalize
from ..database import User
from ..misc import FactionPermission, check_faction_permission

# Anchored on this file rather than on the current working directory, so the
# documents are found wherever the server is started from.
DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "documents"

# Folder names taken from the URL (server, faction): letters, digits, "_" and
# "-" only - in particular no "..", which would climb out of DOCS_DIR.
_SAFE_FOLDER = re.compile(r"^[\w-]+$")

router = APIRouter(prefix="/documents", tags=["Documentation"])


class DocBase(BaseModel):
    title: str
    content: str


def _document_path(*folders: str, doc_name: str) -> Path:
    """Path of a markdown document under DOCS_DIR, or 404.

    `doc_name` is normalized like everywhere else; folder names must be plain
    names, and the resolved path must stay inside DOCS_DIR.
    """
    not_found = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
    )
    if not all(_SAFE_FOLDER.match(folder) for folder in folders):
        raise not_found

    name = normalize(doc_name)
    if not name:
        raise not_found

    path = DOCS_DIR.joinpath(*folders, f"{name}.md").resolve()
    if not path.is_relative_to(DOCS_DIR.resolve()):
        raise not_found
    return path


@router.post(
    "/create",
    response_model=DocBase,
    status_code=status.HTTP_201_CREATED,
)
def create_document(
    doc_info: DocBase,
    current_user: User = Depends(get_current_user),
):
    check_faction_permission(
        current_user,
        FactionPermission.MANAGE_DOCS,
        target_faction_id=current_user.faction_id,
    )

    if not normalize(doc_info.title):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The title must contain at least one letter",
        )

    doc_name = normalize(doc_info.title)
    faction_name = normalize(current_user.faction.name)

    file_path = DOCS_DIR / "AOS" / faction_name / f"{doc_name}.md"
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        file_path.write_text(
            f"# {doc_info.title}\n\n{doc_info.content}", encoding="utf-8"
        )
    except OSError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save document: {e}",
        )

    return doc_info


@router.get(
    "/{server}/doc/{doc_name}",
    response_model=DocBase,
    status_code=status.HTTP_200_OK,
)
def get_document(server: str, doc_name: str):
    file_path = _document_path(server, doc_name=doc_name)

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not read document: {e}",
        )

    return DocBase(title=doc_name, content=content)


@router.get(
    "/{server}/faction_doc/{faction}/{doc_name}",
    response_model=DocBase,
    status_code=status.HTTP_200_OK,
)
def get_faction_document(server: str, faction: str, doc_name: str):
    file_path = _document_path(server, normalize(faction), doc_name=doc_name)

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not read document: {e}",
        )

    return DocBase(title=doc_name, content=content)
