from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..core import get_current_user
from ..crud import normalize
from ..database import User

DOCS_DIR = Path("documents")
router = APIRouter(prefix="/documents", tags=["docs"])


class DocBase(BaseModel):
    title: str
    content: str


@router.post(
    "/create",
    response_model=DocBase,
    status_code=status.HTTP_201_CREATED,
)
def create_document(
    doc_info: DocBase,
    current_user: User = Depends(get_current_user),
):
    if not current_user.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create documents if you are part of a faction.",
        )

    if not current_user.role.manage_docs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have the permissions to create documentation for your faction.",
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
    "/{server}/{faction}/{doc_name}",
    response_model=DocBase,
    status_code=status.HTTP_200_OK,
)
def get_document(server: str, faction: str, doc_name: str):
    file_path = DOCS_DIR / server / normalize(faction) / f"{normalize(doc_name)}.md"

    if not file_path.exists():
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
