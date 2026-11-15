"""Railway lines: readable by everybody, run by train admins and line owners."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import train as crud
from ..database import User, get_db
from ..schemas import LineCreate, LineOut, LineUpdate, StopsUpdate

router = APIRouter(prefix="/lines", tags=["Lines"])


@router.get("", response_model=list[LineOut])
def list_lines(db: Session = Depends(get_db)):
    return crud.list_lines(db)


@router.get("/{code}", response_model=LineOut)
def read_line(code: str, db: Session = Depends(get_db)):
    return crud.get_line(db, code)


@router.post("", response_model=LineOut, status_code=status.HTTP_201_CREATED)
def create_line(
    line_in: LineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.create_line(db, current_user, line_in)


@router.put("/{code}", response_model=LineOut)
def update_line(
    code: str,
    line_in: LineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    line = crud.get_line(db, code)
    crud.check_can_manage_line(current_user, line)
    return crud.update_line(db, current_user, line, line_in)


@router.put("/{code}/stops", response_model=LineOut)
def set_stops(
    code: str,
    stops_in: StopsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Replace the line's stations by this ordered list (first and last = ends)."""
    line = crud.get_line(db, code)
    crud.check_can_manage_line(current_user, line)
    return crud.set_stops(db, line, stops_in)


@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_line(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    line = crud.get_line(db, code)
    crud.check_can_manage_line(current_user, line)
    crud.delete_line(db, line)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
