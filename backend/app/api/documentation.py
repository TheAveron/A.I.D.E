# backend/main.py
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..crud import normalize

DOCS_DIR = Path("documents")
DOCS_DIR.mkdir(exist_ok=True)


router = APIRouter(prefix="/docuements", tags=["create"])


@router.post("/create")
async def create_document(title: str = Form(...), content: str = Form(...)):
    title = normalize(title)

    file_path = DOCS_DIR / f"{title}.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n{content}")
    return {"title": title, "content": content}


@router.get("/documents/{doc_name}")
async def get_document(doc_name: str):
    file_path = DOCS_DIR / f"{doc_name}.md"
    if not file_path.exists():
        return {"error": "Document not found"}
    return file_path.read_text(encoding="utf-8")
