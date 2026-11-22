/**
 * The roles every faction is created with, recognized by their name (same
 * constants as backend/app/misc.py). The server protects them: the leader's
 * can't be changed or deleted, the member's (new members get it) can't be
 * renamed or deleted, and no other role may take these names.
 */
export const LEADER_ROLE = "Chef";
export const MEMBER_ROLE = "Membre";

export const isLeaderRole = (role: { name: string } | null | undefined) =>
    role?.name === LEADER_ROLE;

export const isMemberRole = (role: { name: string } | null | undefined) =>
    role?.name === MEMBER_ROLE;
