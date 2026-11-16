/** What each audit action is called on screen. */
export const AUDIT_LABELS: Record<string, string> = {
    role_granted: "Rôle donné",
    role_revoked: "Rôle retiré",
    password_reset: "Mot de passe réinitialisé",
    user_removed_from_faction: "Retiré d'une faction",
    faction_approved: "Faction approuvée",
    faction_unapproved: "Approbation retirée",
    faction_deleted: "Faction supprimée",
    train_changed: "Train modifié",
    train_retired: "Train retiré",
    line_changed: "Ligne modifiée",
    line_deleted: "Ligne supprimée",
    station_changed: "Gare modifiée",
    station_deleted: "Gare supprimée",
};

export const GLOBAL_ROLE_LABELS: Record<string, string> = {
    admin: "Admin",
    train_admin: "Admin trains",
};

/** The server-wide roles an admin can hand out. */
export const GLOBAL_ROLES = ["admin", "train_admin"] as const;

export const TARGET_LABELS: Record<string, string> = {
    user: "Compte",
    faction: "Faction",
    train: "Train",
    line: "Ligne",
    station: "Gare",
};

/** Where the thing an audit entry is about can be seen, if it still exists. */
export function targetLink(type: string, id: number | null): string | null {
    if (id === null) return null;
    switch (type) {
        case "user":
            return `/user/${id}`;
        case "faction":
            return `/faction/${id}`;
        case "train":
            return `/train/${id}`;
        case "station":
            return `/station/${id}`;
        default:
            return null;
    }
}
