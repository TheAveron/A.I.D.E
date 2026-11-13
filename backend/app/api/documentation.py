import logging
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

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

# Limits on what a faction member may write: a document is a file on the
# server's disk, so its size and the length of its file name are bounded.
MAX_TITLE_LENGTH = 200
MAX_CONTENT_LENGTH = 100_000
MAX_FILENAME_BYTES = 200  # most file systems refuse names over 255 bytes
MAX_DOCUMENTS_PER_FACTION = 200

logger = logging.getLogger("aide")

router = APIRouter(prefix="/documents", tags=["Documentation"])


class DocBase(BaseModel):
    title: str
    content: str


class DocCreate(DocBase):
    """Body of POST /documents/create (the responses use plain DocBase)."""

    title: str = Field(..., max_length=MAX_TITLE_LENGTH)
    content: str = Field(..., max_length=MAX_CONTENT_LENGTH)


def _document_path(*folders: str, doc_name: str) -> Path:
    """Path of a markdown document under DOCS_DIR, or 404.

    `doc_name` is normalized like everywhere else; folder names must be plain
    names, and the resolved path must stay inside DOCS_DIR.
    """
    not_found = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
    )
    if not all(_SAFE_FOLDER.fullmatch(folder) for folder in folders):
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
    doc_info: DocCreate,
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
    if len(doc_name.encode("utf-8")) > MAX_FILENAME_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The title is too long",
        )

    faction_name = normalize(current_user.faction.name)
    if not faction_name or len(faction_name.encode("utf-8")) > MAX_FILENAME_BYTES:
        # An empty name would put the document in the server folder itself.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This faction's name can't be used as a folder name",
        )

    file_path = DOCS_DIR / "AOS" / faction_name / f"{doc_name}.md"

    if file_path.parent.is_dir():
        existing = sum(1 for _ in file_path.parent.glob("*.md"))
        if existing >= MAX_DOCUMENTS_PER_FACTION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A faction can have at most {MAX_DOCUMENTS_PER_FACTION} documents",
            )

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # Mode "x" creates the file or fails: the check and the write are one
        # atomic step, so two requests can't both think they created it.
        with file_path.open("x", encoding="utf-8") as f:
            f.write(f"# {doc_info.title}\n\n{doc_info.content}")
    except FileExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A document with this title already exists",
        )
    except OSError:
        # The OS message contains server paths: log it, don't send it.
        logger.exception("Could not save document %s", file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the document",
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
    except OSError:
        logger.exception("Could not read document %s", file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not read the document",
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
    except OSError:
        logger.exception("Could not read document %s", file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not read the document",
        )

    return DocBase(title=doc_name, content=content)
