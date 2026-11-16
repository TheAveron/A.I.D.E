"""An account's own preferences: nobody reads or changes anybody else's."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import preferences as crud
from ..database import User, get_db
from ..schemas import PreferencesOut, PreferencesUpdate

router = APIRouter(prefix="/preferences", tags=["Preferences"])


@router.get("", response_model=PreferencesOut)
def read_preferences(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return crud.get_preferences(db, current_user.user_id)


@router.put("", response_model=PreferencesOut)
def update_preferences(
    body: PreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change what was sent; the rest stays as it was."""
    row = crud.save_preferences(
        db, current_user.user_id, body.model_dump(exclude_unset=True)
    )
    db.commit()
    db.refresh(row)
    return row
