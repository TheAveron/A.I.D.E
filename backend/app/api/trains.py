"""The index of trains: readable by everybody; any account registers its own."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import train as crud
from ..database import User, get_db
from ..misc import TrainService
from ..schemas import TrainCreate, TrainHistoryOut, TrainOut, TrainUpdate

router = APIRouter(prefix="/trains", tags=["Trains"])


@router.get("", response_model=list[TrainOut])
def list_trains(
    line: Optional[str] = Query(None, max_length=2, description="A, A2, Z..."),
    service: Optional[TrainService] = None,
    owner_user_id: Optional[int] = None,
    owner_faction_id: Optional[int] = None,
    q: Optional[str] = Query(None, max_length=50, description="Name or old name"),
    include_retired: bool = False,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    db: Session = Depends(get_db),
):
    return crud.list_trains(
        db,
        line=line,
        service=service.value if service else None,
        owner_user_id=owner_user_id,
        owner_faction_id=owner_faction_id,
        search=q,
        include_retired=include_retired,
        skip=skip,
        limit=limit,
    )


@router.get("/{train_id}", response_model=TrainOut)
def read_train(train_id: int, db: Session = Depends(get_db)):
    return crud.get_train(db, train_id)


@router.get("/{train_id}/history", response_model=list[TrainHistoryOut])
def read_history(train_id: int, db: Session = Depends(get_db)):
    return crud.get_train(db, train_id).history


@router.post("", response_model=TrainOut, status_code=status.HTTP_201_CREATED)
def create_train(
    train_in: TrainCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register a train. The number is attributed here and comes back in the answer."""
    return crud.create_train(db, current_user, train_in)


@router.put("/{train_id}", response_model=TrainOut)
def update_train(
    train_id: int,
    train_in: TrainUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    train = crud.get_train(db, train_id)
    crud.check_can_manage_train(current_user, train)
    return crud.update_train(db, current_user, train, train_in)


@router.delete("/{train_id}", status_code=status.HTTP_204_NO_CONTENT)
def retire_train(
    train_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Take a train out of service: its number is freed, its history stays."""
    train = crud.get_train(db, train_id)
    crud.check_can_manage_train(current_user, train)
    crud.retire_train(db, current_user, train)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
