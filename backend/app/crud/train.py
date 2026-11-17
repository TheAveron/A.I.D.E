"""Lines, trains and their history.

Who may do what:
- any account registers a train in its own name; a train of a faction needs
  `manage_trains` in that faction;
- a train is changed or retired by its owner (a faction's trains: by members
  with `manage_trains`) and by train admins, who may change everything;
- lines are created and changed by train admins and by `manage_trains`
  members of the faction that looks after them.

Every function that writes commits; names and numbers are rebuilt here, never
typed by hand.
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import (Faction, GlobalRoleName, Line, LineStop, Station,
                        Train, TrainHistory, User)
from ..database.clock import utcnow
from ..database.models.train import MAINTENANCE_LINE
from ..misc import FactionPermission, TrainAction, check_faction_permission
from ..schemas import (LineCreate, LineUpdate, StopsUpdate, TrainCreate,
                       TrainUpdate)

MAX_NUMBER = 99
# Attempts when two requests grab the same free number at once
NUMBER_RETRIES = 5


def _error(code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=code, detail=detail)


def is_train_admin(user: User) -> bool:
    return user.has_global_role(GlobalRoleName.TRAIN_ADMIN.value)


def holds_manage_trains(user: User, faction_id: Optional[int]) -> bool:
    """Whether `user` holds `manage_trains` in the faction `faction_id`."""
    if faction_id is None:
        return False
    try:
        check_faction_permission(
            user, FactionPermission.MANAGE_TRAINS, target_faction_id=faction_id
        )
    except HTTPException:
        return False
    return True


def _live_faction(db: Session, faction_id: int) -> Faction:
    faction = (
        db.query(Faction)
        .filter(Faction.faction_id == faction_id, Faction.deleted_at.is_(None))
        .first()
    )
    if not faction:
        raise _error(status.HTTP_404_NOT_FOUND, "Faction not found")
    return faction


# ---- lines ----


def get_line(db: Session, code: str) -> Line:
    line = db.query(Line).filter(Line.code == code.strip().upper()).first()
    if not line:
        raise _error(status.HTTP_404_NOT_FOUND, f"Line {code} not found")
    return line


def list_lines(db: Session) -> list[Line]:
    return db.query(Line).order_by(Line.code).all()


def can_manage_line(user: User, line: Line) -> bool:
    return is_train_admin(user) or holds_manage_trains(user, line.owner_faction_id)


def check_can_manage_line(user: User, line: Line) -> None:
    if not can_manage_line(user, line):
        raise _error(
            status.HTTP_403_FORBIDDEN,
            "Only a train admin or the faction in charge of the line can change it",
        )


def create_line(db: Session, user: User, data: LineCreate) -> Line:
    admin = is_train_admin(user)
    owner_id = data.owner_faction_id
    if owner_id is None and not admin:
        owner_id = user.faction_id
    if owner_id is not None:
        _live_faction(db, owner_id)
    if not admin and not holds_manage_trains(user, owner_id):
        raise _error(
            status.HTTP_403_FORBIDDEN,
            "Creating a line needs the train admin role or manage_trains "
            "in the faction that will look after it",
        )
    line = Line(
        code=data.code,
        name=data.name,
        color=data.color,
        description=data.description,
        owner_faction_id=owner_id,
        created_by_user_id=user.user_id,
    )
    db.add(line)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _error(status.HTTP_409_CONFLICT, f"The line {data.code} already exists")
    db.refresh(line)
    return line


def update_line(db: Session, user: User, line: Line, data: LineUpdate) -> Line:
    changes = data.model_dump(exclude_unset=True)
    if "owner_faction_id" in changes:
        if not is_train_admin(user):
            raise _error(
                status.HTTP_403_FORBIDDEN,
                "Only a train admin can hand a line over to another faction",
            )
        if changes["owner_faction_id"] is not None:
            _live_faction(db, changes["owner_faction_id"])
    for field, value in changes.items():
        setattr(line, field, value)
    db.commit()
    db.refresh(line)
    return line


def set_stops(db: Session, line: Line, data: StopsUpdate) -> Line:
    if line.code == MAINTENANCE_LINE:
        raise _error(status.HTTP_409_CONFLICT, "The maintenance line has no stations")
    found = {
        station_id
        for (station_id,) in db.query(Station.station_id).filter(
            Station.station_id.in_(data.station_ids)
        )
    }
    missing = [i for i in data.station_ids if i not in found]
    if missing:
        raise _error(status.HTTP_404_NOT_FOUND, f"Unknown stations: {missing}")
    # A bulk delete runs now: the unit of work would insert before deleting and
    # trip over the (line, station) uniqueness for stations that stay.
    db.query(LineStop).filter(LineStop.line_id == line.line_id).delete(
        synchronize_session=False
    )
    db.expire(line, ["stops"])
    for position, station_id in enumerate(data.station_ids):
        db.add(LineStop(line_id=line.line_id, station_id=station_id, position=position))
    db.commit()
    db.expire(line, ["stops"])
    db.refresh(line)
    return line


def delete_line(db: Session, line: Line) -> None:
    if line.code == MAINTENANCE_LINE:
        raise _error(status.HTTP_409_CONFLICT, "The maintenance line cannot be deleted")
    if db.query(Train).filter(Train.line_id == line.line_id).first():
        raise _error(
            status.HTTP_409_CONFLICT,
            "Trains still belong (or belonged) to this line: move them first",
        )
    db.delete(line)
    db.commit()


def _maintenance_line(db: Session) -> Line:
    """The line Z, created the first time somebody needs it."""
    line = db.query(Line).filter(Line.code == MAINTENANCE_LINE).first()
    if line is None:
        line = Line(code=MAINTENANCE_LINE, name="Entretien")
        db.add(line)
        try:
            db.flush()
        except IntegrityError:  # created by a concurrent request
            db.rollback()
            line = db.query(Line).filter(Line.code == MAINTENANCE_LINE).one()
    return line


def _line_for_trains(db: Session, code: str) -> Line:
    if code == MAINTENANCE_LINE:
        return _maintenance_line(db)
    line = db.query(Line).filter(Line.code == code).first()
    if not line:
        raise _error(
            status.HTTP_404_NOT_FOUND,
            f"The line {code} does not exist: ask for it to be created first",
        )
    return line


# ---- trains ----


def get_train(db: Session, train_id: int) -> Train:
    train = db.query(Train).filter(Train.train_id == train_id).first()
    if not train:
        raise _error(status.HTTP_404_NOT_FOUND, "Train not found")
    return train


def list_trains(
    db: Session,
    line: Optional[str] = None,
    service: Optional[str] = None,
    owner_user_id: Optional[int] = None,
    owner_faction_id: Optional[int] = None,
    search: Optional[str] = None,
    include_retired: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> list[Train]:
    query = db.query(Train).join(Line, Line.line_id == Train.line_id)
    if not include_retired:
        query = query.filter(Train.retired_at.is_(None))
    if line:
        query = query.filter(Line.code == line.strip().upper())
    if service:
        query = query.filter(Train.service == service)
    if owner_user_id is not None:
        query = query.filter(Train.owner_user_id == owner_user_id)
    if owner_faction_id is not None:
        query = query.filter(Train.owner_faction_id == owner_faction_id)
    if search and search.strip():
        escaped = (
            search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        pattern = f"%{escaped}%"
        query = query.filter(
            Train.common_name.ilike(pattern, escape="\\")
            | Train.legacy_id.ilike(pattern, escape="\\")
        )
    return (
        query.order_by(Line.code, Train.number, Train.train_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def can_manage_train(user: User, train: Train) -> bool:
    if is_train_admin(user):
        return True
    if train.owner_user_id is not None:
        return train.owner_user_id == user.user_id
    return holds_manage_trains(user, train.owner_faction_id)


def is_train_override(user: User, train: Train) -> bool:
    """A train admin acting on a train they would not otherwise manage."""
    if not is_train_admin(user):
        return False
    if train.owner_user_id is not None:
        return train.owner_user_id != user.user_id
    return not holds_manage_trains(user, train.owner_faction_id)


def is_line_override(user: User, line: Line) -> bool:
    return is_train_admin(user) and not holds_manage_trains(user, line.owner_faction_id)


def check_can_manage_train(user: User, train: Train) -> None:
    if not can_manage_train(user, train):
        raise _error(
            status.HTTP_403_FORBIDDEN,
            "Only the owner (or a train admin) can change this train",
        )


def _first_free_number(
    db: Session, line_id: int, exclude_train_id: Optional[int] = None
) -> int:
    query = db.query(Train.number).filter(
        Train.line_id == line_id, Train.retired_at.is_(None)
    )
    if exclude_train_id is not None:
        query = query.filter(Train.train_id != exclude_train_id)
    used = {number for (number,) in query}
    for number in range(1, MAX_NUMBER + 1):
        if number not in used:
            return number
    raise _error(
        status.HTTP_409_CONFLICT,
        "All 99 numbers of this line are taken"
        + (
            ": create a branch (A2, A3...)"
            if len(db.get(Line, line_id).code) == 1
            else ""
        ),
    )


def _check_legacy_free(
    db: Session, legacy_id: Optional[str], exclude_train_id: Optional[int] = None
) -> None:
    if not legacy_id:
        return
    query = db.query(Train).filter(
        func.lower(Train.legacy_id) == legacy_id.lower(), Train.retired_at.is_(None)
    )
    if exclude_train_id is not None:
        query = query.filter(Train.train_id != exclude_train_id)
    if query.first():
        raise _error(
            status.HTTP_409_CONFLICT,
            f"Another train already has the old name {legacy_id}",
        )


def _record(
    db: Session,
    train: Train,
    action: TrainAction,
    actor: User,
    old_name: Optional[str],
    new_name: Optional[str],
) -> None:
    db.add(
        TrainHistory(
            train=train,
            action=action.value,
            old_name=old_name,
            new_name=new_name,
            actor_user_id=actor.user_id,
        )
    )


def _resolve_new_owner(
    db: Session,
    user: User,
    owner_user_id: Optional[int],
    owner_faction_id: Optional[int],
) -> tuple[Optional[int], Optional[int]]:
    """Check that `user` may register / hand a train to this owner.

    Without a train admin's say-so, a train can only go to oneself or to a
    faction where one holds manage_trains: nobody receives a train they did
    not accept.
    """
    admin = is_train_admin(user)
    if owner_faction_id is not None:
        _live_faction(db, owner_faction_id)
        if not admin and not holds_manage_trains(user, owner_faction_id):
            raise _error(
                status.HTTP_403_FORBIDDEN,
                "A faction's trains need manage_trains in that faction",
            )
        return None, owner_faction_id
    if owner_user_id is None or owner_user_id == user.user_id:
        return user.user_id, None
    if not admin:
        raise _error(
            status.HTTP_403_FORBIDDEN, "You can only register trains in your own name"
        )
    if not db.query(User).filter(User.user_id == owner_user_id).first():
        raise _error(status.HTTP_404_NOT_FOUND, "Owner not found")
    return owner_user_id, None


def _place_train(db: Session, train: Train, line: Line, keep_number: bool) -> None:
    """Put `train` on `line` and flush it, taking the first free number.

    Everything happens inside a savepoint, and the number is computed before
    the train is attached to the line, so no half-built state is ever sent to
    the database. The partial unique index decides when two requests race for
    the same number: the loser rolls back to the savepoint and takes the next
    free one.
    """
    for _ in range(NUMBER_RETRIES):
        try:
            with db.begin_nested():
                if not keep_number:
                    # Creators on the same line queue up here (PostgreSQL;
                    # SQLite ignores it), so they rarely race for a number.
                    db.query(Line.line_id).filter(
                        Line.line_id == line.line_id
                    ).with_for_update().first()
                number = (
                    train.number
                    if keep_number
                    else _first_free_number(db, line.line_id, train.train_id)
                )
                train.line = line
                train.number = number
                db.add(train)
                db.flush()
            return
        except IntegrityError:
            if keep_number:
                break
    raise _error(
        status.HTTP_409_CONFLICT, "This number is already taken on the line, retry"
    )


def create_train(db: Session, user: User, data: TrainCreate) -> Train:
    owner_user_id, owner_faction_id = _resolve_new_owner(
        db, user, data.owner_user_id, data.owner_faction_id
    )
    line = _line_for_trains(db, data.line)
    _check_legacy_free(db, data.legacy_id)
    train = Train(
        service=data.service.value if data.service else None,
        number=0,
        common_name=data.common_name or None,
        legacy_id=data.legacy_id or None,
        owner_user_id=owner_user_id,
        owner_faction_id=owner_faction_id,
        created_by_user_id=user.user_id,
    )
    _place_train(db, train, line, keep_number=False)
    db.refresh(train)
    _record(db, train, TrainAction.CREATED, user, None, train.display_name)
    db.commit()
    db.refresh(train)
    return train


def update_train(db: Session, user: User, train: Train, data: TrainUpdate) -> Train:
    if train.retired_at is not None:
        raise _error(status.HTTP_409_CONFLICT, "This train is retired")
    changes = data.model_dump(exclude_unset=True)
    old_name = train.display_name
    old_owner = (train.owner_user_id, train.owner_faction_id)

    line = train.line
    new_line = line
    if "line" in changes and changes["line"] != line.code:
        new_line = _line_for_trains(db, changes["line"])
    new_service = (
        changes["service"].value
        if changes.get("service") is not None
        else (None if "service" in changes else train.service)
    )
    if new_line.code == MAINTENANCE_LINE and new_service is not None:
        raise _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Maintenance trains (line Z) have no service",
        )
    if new_line.code != MAINTENANCE_LINE and new_service is None:
        raise _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "A service (O, E, F or L) is required outside line Z",
        )

    if "legacy_id" in changes:
        _check_legacy_free(db, changes["legacy_id"], train.train_id)
        train.legacy_id = changes["legacy_id"] or None
    if "common_name" in changes:
        train.common_name = changes["common_name"] or None

    if "owner_user_id" in changes or "owner_faction_id" in changes:
        owner_user_id, owner_faction_id = _resolve_new_owner(
            db,
            user,
            changes.get("owner_user_id"),
            changes.get("owner_faction_id"),
        )
        if "owner_user_id" in changes and "owner_faction_id" in changes:
            if owner_user_id is None and owner_faction_id is None:
                raise _error(
                    status.HTTP_422_UNPROCESSABLE_ENTITY, "A train needs an owner"
                )
        train.owner_user_id = owner_user_id
        train.owner_faction_id = owner_faction_id

    train.service = new_service
    _place_train(db, train, new_line, keep_number=new_line is line)
    db.refresh(train)

    new_name = train.display_name
    if new_name != old_name or old_owner != (
        train.owner_user_id,
        train.owner_faction_id,
    ):
        _record(db, train, TrainAction.UPDATED, user, old_name, new_name)
    train.updated_at = utcnow()
    db.commit()
    db.refresh(train)
    return train


def retire_train(db: Session, user: User, train: Train) -> None:
    if train.retired_at is not None:
        raise _error(status.HTTP_409_CONFLICT, "This train is already retired")
    train.retired_at = utcnow()
    _record(db, train, TrainAction.RETIRED, user, train.display_name, None)
    db.commit()
