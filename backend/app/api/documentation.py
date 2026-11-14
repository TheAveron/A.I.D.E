import logging
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import faction as faction_crud
from ..crud import normalize
from ..database import User, get_db
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

# Faction documents are written under this server's folder.
FACTION_DOCS_SERVER = "AOS"

logger = logging.getLogger("aide")

router = APIRouter(prefix="/documents", tags=["Documentation"])


class DocBase(BaseModel):
    title: str
    content: str


class DocSummary(BaseModel):
    """A faction document in a listing: where to open it, and its title."""

    server: str
    folder: str
    doc_name: str
    title: str


class DocCreate(DocBase):
    """Body of POST /documents/create (the responses use plain DocBase)."""

    title: str = Field(..., max_length=MAX_TITLE_LENGTH)
    content: str = Field(..., max_length=MAX_CONTENT_LENGTH)


def move_faction_folder(old_name: str, new_name: str) -> bool:
    """Move a faction's documents folder after the faction was renamed.

    The folder is named after `normalize(name)`, so a rename that changes it
    would otherwise leave the documents behind. Returns whether a folder was
    moved; raises 409 when the new name's folder is already taken (documents
    of a deleted faction, say) rather than mixing the two.
    """
    old_folder, new_folder = normalize(old_name), normalize(new_name)
    if old_folder == new_folder:
        return False

    root = DOCS_DIR.resolve() / FACTION_DOCS_SERVER
    source = root / old_folder
    target = root / new_folder
    if (
        not old_folder
        or not new_folder
        or not _SAFE_FOLDER.fullmatch(old_folder)
        or not _SAFE_FOLDER.fullmatch(new_folder)
        or not source.is_dir()
    ):
        return False
    if target.exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A documents folder already exists for this name",
        )
    try:
        source.rename(target)
    except OSError:
        logger.exception("Could not move documents %s -> %s", source, target)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not move the faction's documents",
        )
    return True


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

    file_path = DOCS_DIR / FACTION_DOCS_SERVER / faction_name / f"{doc_name}.md"

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


def _title_of(path: Path) -> str:
    """Title of a document: its first "# " heading, else its file name."""
    try:
        with path.open(encoding="utf-8") as f:
            first_line = f.readline().strip()
    except (OSError, UnicodeDecodeError):
        first_line = ""
    if first_line.startswith("# ") and first_line[2:].strip():
        return first_line[2:].strip()
    return path.stem


@router.get(
    "/faction/{faction_id}",
    response_model=list[DocSummary],
    status_code=status.HTTP_200_OK,
)
def list_faction_documents(faction_id: int, db: Session = Depends(get_db)):
    """The documents a faction has written, by file name."""
    faction = faction_crud.get_faction(db, faction_id)
    if not faction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Faction not found"
        )

    folder = normalize(faction.name)
    if not folder or not _SAFE_FOLDER.fullmatch(folder):
        return []
    directory = (DOCS_DIR / FACTION_DOCS_SERVER / folder).resolve()
    if not directory.is_relative_to(DOCS_DIR.resolve()) or not directory.is_dir():
        return []

    files = sorted(directory.glob("*.md"))[:MAX_DOCUMENTS_PER_FACTION]
    return [
        DocSummary(
            server=FACTION_DOCS_SERVER,
            folder=folder,
            doc_name=path.stem,
            title=_title_of(path),
        )
        for path in files
        if path.is_file()
    ]


def _faction_folder(db: Session, faction_id: int) -> Path:
    """The folder of a faction's documents, or 404 for an unknown faction."""
    faction = faction_crud.get_faction(db, faction_id)
    if not faction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Faction not found"
        )
    folder = normalize(faction.name)
    if not folder or not _SAFE_FOLDER.fullmatch(folder):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    return DOCS_DIR.resolve() / FACTION_DOCS_SERVER / folder


def _split_title(text: str, fallback: str) -> tuple[str, str]:
    """A stored document as (title, body): the "# " first line is the title."""
    first, _, rest = text.partition("\n")
    if first.startswith("# ") and first[2:].strip():
        return first[2:].strip(), rest.lstrip("\n")
    return fallback, text


@router.get(
    "/faction/{faction_id}/{doc_name}",
    response_model=DocBase,
    status_code=status.HTTP_200_OK,
)
def get_faction_document_for_edit(
    faction_id: int, doc_name: str, db: Session = Depends(get_db)
):
    """A faction document split into its title and body (for an editor)."""
    folder = _faction_folder(db, faction_id)
    path = _document_path(FACTION_DOCS_SERVER, folder.name, doc_name=doc_name)
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        logger.exception("Could not read document %s", path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not read the document",
        )
    title, body = _split_title(text, path.stem)
    return DocBase(title=title, content=body)


@router.put(
    "/faction/{faction_id}/{doc_name}",
    response_model=DocBase,
    status_code=status.HTTP_200_OK,
)
def update_document(
    faction_id: int,
    doc_name: str,
    doc_info: DocCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rewrite a document of one's faction; a new title renames its file."""
    check_faction_permission(
        current_user, FactionPermission.MANAGE_DOCS, target_faction_id=faction_id
    )
    folder = _faction_folder(db, faction_id)
    path = _document_path(FACTION_DOCS_SERVER, folder.name, doc_name=doc_name)
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    new_name = normalize(doc_info.title)
    if not new_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The title must contain at least one letter",
        )
    if len(new_name.encode("utf-8")) > MAX_FILENAME_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="The title is too long"
        )

    target = path.with_name(f"{new_name}.md")
    text = f"# {doc_info.title}\n\n{doc_info.content}"
    try:
        if target == path:
            # Replace atomically: a crash must not leave half a document.
            tmp = path.with_name(f".{path.name}.tmp")
            tmp.write_text(text, encoding="utf-8")
            tmp.replace(path)
        else:
            with target.open("x", encoding="utf-8") as f:
                f.write(text)
            path.unlink()
    except FileExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A document with this title already exists",
        )
    except OSError:
        logger.exception("Could not save document %s", path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the document",
        )
    return doc_info


@router.delete(
    "/faction/{faction_id}/{doc_name}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_document(
    faction_id: int,
    doc_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document of one's faction."""
    check_faction_permission(
        current_user, FactionPermission.MANAGE_DOCS, target_faction_id=faction_id
    )
    folder = _faction_folder(db, faction_id)
    path = _document_path(FACTION_DOCS_SERVER, folder.name, doc_name=doc_name)
    try:
        path.unlink()
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    except OSError:
        logger.exception("Could not delete document %s", path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not delete the document",
        )
    return None


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
