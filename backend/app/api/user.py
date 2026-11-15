from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import faction as crud_faction
from ..crud import faction_role as crud_role
from ..crud import user as crud_user
from ..crud.notification import notify
from ..database import User, get_db
from ..misc import FactionPermission, check_faction_permission
from ..schemas import UserFull, UserOut, UserPublic, UserUpdate

NO_FACTION_NAME = "Sans Faction"
GUEST_ROLE_NAME = "Invité"
MEMBER_ROLE_NAME = "Membre"
LEADER_ROLE_NAME = "Chef"

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserFull, status_code=status.HTTP_200_OK)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/faction/{faction_id}", response_model=list[UserPublic])
def get_users_by_faction(faction_id: int, db: Session = Depends(get_db)):
    users = crud_user.get_users_by_faction(db, faction_id)
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error getting user list for faction: {faction_id}",
        )
    return users


@router.get(
    "/from_name/{username}", response_model=UserPublic, status_code=status.HTTP_200_OK
)
def read_user_by_name(username: str, db: Session = Depends(get_db)):
    user = crud_user.get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.get(
    "/detail/{user_id}", response_model=UserPublic, status_code=status.HTTP_200_OK
)
def read_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = crud_user.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


def _join_faction(
    db: Session, user: User, faction_id: int | None, role_id: int | None
) -> User:
    """A user asking to join a faction for themselves.

    The role is never chosen by the client: joining always lands on the
    target faction's guest role, whatever role_id was sent (a different
    role_id is refused rather than silently ignored).
    """
    if faction_id is None:
        if role_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can't change your own role",
            )
        return user  # nothing to change

    faction = crud_faction.get_faction(db, faction_id)
    if not faction or faction.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Faction not found")

    if faction.name == NO_FACTION_NAME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This faction can't be joined",
        )

    if user.faction_id == faction.faction_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already belong to this faction",
        )

    if faction.requires_approval:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This faction only takes members through a join request",
        )

    current_faction_name = user.faction.name if user.faction else None
    if (
        user.role
        and user.role.name == LEADER_ROLE_NAME
        and current_faction_name != NO_FACTION_NAME
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A faction leader can't leave their faction",
        )

    guest_role = next(
        (
            r
            for r in crud_role.get_roles_by_faction(db, faction.faction_id)
            if r.name == GUEST_ROLE_NAME
        ),
        None,
    )
    if not guest_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This faction has no guest role to join with",
        )

    if role_id is not None and role_id != guest_role.role_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only join a faction as a guest",
        )

    return crud_user.update_user_faction_and_role(
        db, user.user_id, faction.faction_id, guest_role.role_id
    )


def _assign_role(
    db: Session,
    actor: User,
    target: User,
    faction_id: int | None,
    role_id: int | None,
) -> User:
    """A member with `handle_members` changing another member's role."""
    check_faction_permission(actor, FactionPermission.HANDLE_MEMBERS)

    if target.faction_id != actor.faction_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage members of your own faction",
        )

    if faction_id is not None and faction_id != target.faction_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Members can't be moved to another faction",
        )

    if role_id is None:
        return target  # nothing to change

    if target.role and target.role.name == LEADER_ROLE_NAME:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The faction leader's role can't be changed",
        )

    role = crud_role.get_role_by_id(db, role_id)
    if not role or role.faction_id != actor.faction_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found in your faction",
        )

    if role.name == LEADER_ROLE_NAME:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The leader role can't be assigned",
        )

    # Nobody hands out powers they don't hold themselves.
    for permission in FactionPermission:
        if role.has_permission(permission.value) and not actor.role.has_permission(
            permission.value
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can't assign a role with permissions you don't have",
            )

    notify(
        db,
        target.user_id,
        "role_changed",
        f"{actor.username} vous a donné le rôle « {role.name} »",
        f"/faction/{role.faction_id}",
    )
    return crud_user.update_user_faction_and_role(
        db, target.user_id, None, role.role_id
    )


@router.patch("/update/{user_id}", response_model=UserOut)
def update_role_faction(
    user_id: int,
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Join a faction (own account) or change a member's role.

    - own account: `faction_id` = join that faction as a guest; `role_id`
      can't be chosen.
    - another member: requires `handle_members` in the same faction; only
      `role_id` (a non-leader role of that faction, with no more powers than
      the caller) can be changed.
    """
    target = crud_user.get_user_by_id(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if user_id == current_user.user_id:
        return _join_faction(
            db, current_user, update_data.faction_id, update_data.role_id
        )

    return _assign_role(
        db, current_user, target, update_data.faction_id, update_data.role_id
    )


def _send_to_no_faction(db: Session, user: User) -> User:
    """Put a user back in "Sans Faction", with the role new accounts get."""
    no_faction = crud_faction.get_faction_by_name(db, NO_FACTION_NAME)
    role = None
    if no_faction:
        role = next(
            (
                r
                for r in crud_role.get_roles_by_faction(db, no_faction.faction_id)
                if r.name == MEMBER_ROLE_NAME
            ),
            None,
        )
    if not no_faction or not role:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f'The "{NO_FACTION_NAME}" faction is not set up',
        )
    return crud_user.update_user_faction_and_role(
        db, user.user_id, no_faction.faction_id, role.role_id
    )


def _in_a_real_faction(user: User) -> bool:
    return bool(user.faction and user.faction.name != NO_FACTION_NAME)


@router.post("/leave", response_model=UserOut)
def leave_faction(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Leave one's faction and go back to "Sans Faction"; a leader can't."""
    if not _in_a_real_faction(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You don't belong to a faction",
        )
    if current_user.role and current_user.role.name == LEADER_ROLE_NAME:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A faction leader can't leave their faction",
        )
    return _send_to_no_faction(db, current_user)


@router.post("/{user_id}/kick", response_model=UserOut)
def kick_member(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a member from one's faction (needs `handle_members`).

    The leader can't be removed, and nobody removes a member who holds
    powers they don't hold themselves (the rule that also limits role
    assignment).
    """
    check_faction_permission(current_user, FactionPermission.HANDLE_MEMBERS)

    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use /users/leave to leave your own faction",
        )

    target = crud_user.get_user_by_id(db, user_id)
    if not target or target.faction_id != current_user.faction_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in your faction",
        )

    if not _in_a_real_faction(target):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user doesn't belong to a faction",
        )

    if target.role and target.role.name == LEADER_ROLE_NAME:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The faction leader can't be removed",
        )

    if target.role:
        for permission in FactionPermission:
            if target.role.has_permission(
                permission.value
            ) and not current_user.role.has_permission(permission.value):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can't remove a member with permissions you don't have",
                )

    notify(
        db,
        target.user_id,
        "kicked",
        f"{current_user.username} vous a exclu de {target.faction.name}",
        "/factions",
    )
    return _send_to_no_faction(db, target)
