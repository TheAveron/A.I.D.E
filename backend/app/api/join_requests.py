"""Requests to join a faction that only takes members on request.

A faction with `requires_approval` can't be joined directly (PATCH
/users/update/{id}); the applicant asks here and a member holding
`handle_members` accepts or refuses. Accepting is what moves the applicant
into the faction, as a guest, exactly like a direct join would.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import faction as crud_faction
from ..crud import faction_role as crud_role
from ..crud.notification import members_with_permission, notify, notify_many
from ..database import JoinRequest, User, get_db
from ..database.clock import utcnow
from ..misc import (GUEST_ROLE_NAME, LEADER_ROLE_NAME, FactionPermission,
                    JoinRequestStatus, check_faction_permission)
from ..schemas import JoinRequestCreate, JoinRequestOut

NO_FACTION_NAME = "Sans Faction"

router = APIRouter(prefix="/join_requests", tags=["Join requests"])


def _is_leader_of_a_real_faction(user: User) -> bool:
    return bool(
        user.role
        and user.role.name == LEADER_ROLE_NAME
        and user.faction
        and user.faction.name != NO_FACTION_NAME
    )


def _get_pending(db: Session, request_id: int) -> JoinRequest:
    join_request = (
        db.query(JoinRequest).filter(JoinRequest.request_id == request_id).first()
    )
    if not join_request:
        raise HTTPException(status_code=404, detail="Join request not found")
    if join_request.status != JoinRequestStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This request has already been dealt with",
        )
    return join_request


def _close(join_request: JoinRequest, new_status: JoinRequestStatus, by: User) -> None:
    join_request.status = new_status.value
    join_request.decided_at = utcnow()
    join_request.decided_by_user_id = by.user_id


@router.post("", response_model=JoinRequestOut, status_code=status.HTTP_201_CREATED)
def create_join_request(
    body: JoinRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    faction = crud_faction.get_faction(db, body.faction_id)
    if not faction or faction.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Faction not found")

    if faction.name == NO_FACTION_NAME:
        raise HTTPException(status_code=400, detail="This faction can't be joined")

    if current_user.faction_id == faction.faction_id:
        raise HTTPException(
            status_code=400, detail="You already belong to this faction"
        )

    if not faction.requires_approval:
        raise HTTPException(
            status_code=400,
            detail="This faction can be joined directly, no request needed",
        )

    if _is_leader_of_a_real_faction(current_user):
        raise HTTPException(
            status_code=403, detail="A faction leader can't leave their faction"
        )

    message = (body.message or "").strip() or None
    join_request = JoinRequest(
        user_id=current_user.user_id,
        faction_id=faction.faction_id,
        status=JoinRequestStatus.PENDING.value,
        message=message,
    )
    db.add(join_request)
    notify_many(
        db,
        members_with_permission(
            db, faction.faction_id, FactionPermission.HANDLE_MEMBERS
        ),
        "join_request",
        f"{current_user.username} demande à rejoindre {faction.name}",
        f"/faction/{faction.faction_id}",
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending request: withdraw it first",
        )
    db.refresh(join_request)
    return join_request


@router.get("/mine", response_model=JoinRequestOut | None)
def my_pending_request(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """The caller's open request, or null."""
    return (
        db.query(JoinRequest)
        .filter(
            JoinRequest.user_id == current_user.user_id,
            JoinRequest.status == JoinRequestStatus.PENDING.value,
        )
        .first()
    )


@router.get("/faction/{faction_id}", response_model=list[JoinRequestOut])
def faction_pending_requests(
    faction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Open requests to join a faction, oldest first (for its member managers)."""
    check_faction_permission(
        current_user, FactionPermission.HANDLE_MEMBERS, target_faction_id=faction_id
    )
    return (
        db.query(JoinRequest)
        .filter(
            JoinRequest.faction_id == faction_id,
            JoinRequest.status == JoinRequestStatus.PENDING.value,
        )
        .order_by(JoinRequest.created_at, JoinRequest.request_id)
        .all()
    )


@router.post("/{request_id}/accept", response_model=JoinRequestOut)
def accept_join_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    join_request = _get_pending(db, request_id)
    check_faction_permission(
        current_user,
        FactionPermission.HANDLE_MEMBERS,
        target_faction_id=join_request.faction_id,
    )

    applicant = join_request.user
    guest_role = next(
        (
            role
            for role in crud_role.get_roles_by_faction(db, join_request.faction_id)
            if role.name == GUEST_ROLE_NAME
        ),
        None,
    )
    if not guest_role:
        raise HTTPException(
            status_code=400, detail="This faction has no guest role to join with"
        )

    if _is_leader_of_a_real_faction(applicant):
        # Became a leader elsewhere since asking: the request can't be honoured.
        _close(join_request, JoinRequestStatus.CANCELLED, current_user)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The applicant now leads another faction",
        )

    # The move and the closing of the request are one transaction.
    applicant.faction_id = join_request.faction_id
    applicant.role_id = guest_role.role_id
    _close(join_request, JoinRequestStatus.ACCEPTED, current_user)
    notify(
        db,
        applicant.user_id,
        "join_accepted",
        f"Votre demande pour rejoindre {join_request.faction.name} a été acceptée",
        f"/faction/{join_request.faction_id}",
    )
    db.commit()
    db.refresh(join_request)
    return join_request


@router.post("/{request_id}/refuse", response_model=JoinRequestOut)
def refuse_join_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    join_request = _get_pending(db, request_id)
    check_faction_permission(
        current_user,
        FactionPermission.HANDLE_MEMBERS,
        target_faction_id=join_request.faction_id,
    )
    _close(join_request, JoinRequestStatus.REFUSED, current_user)
    notify(
        db,
        join_request.user_id,
        "join_refused",
        f"Votre demande pour rejoindre {join_request.faction.name} a été refusée",
        "/factions",
    )
    db.commit()
    db.refresh(join_request)
    return join_request


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def withdraw_join_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The applicant withdraws their own open request."""
    join_request = _get_pending(db, request_id)
    if join_request.user_id != current_user.user_id:
        raise HTTPException(
            status_code=403, detail="You can only withdraw your own request"
        )
    _close(join_request, JoinRequestStatus.CANCELLED, current_user)
    db.commit()
