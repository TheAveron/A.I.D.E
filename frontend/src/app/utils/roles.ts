/**
 * The roles every faction is created with, recognized by their name (same
 * constants as backend/app/misc.py). The server protects them: the leader's
 * can't be changed or deleted, the guest's can't be renamed or deleted, and
 * no other role may take these names.
 */
export const LEADER_ROLE = "Chef";
export const GUEST_ROLE = "Invité";

export const isLeaderRole = (role: { name: string } | null | undefined) =>
    role?.name === LEADER_ROLE;

export const isGuestRole = (role: { name: string } | null | undefined) =>
    role?.name === GUEST_ROLE;
