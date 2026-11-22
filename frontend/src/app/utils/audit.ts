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
    territory_changed: "Territoire modifié",
    territory_deleted: "Territoire supprimé",
    marker_changed: "Point de carte modifié",
    marker_deleted: "Point de carte supprimé",
    offer_cancelled: "Offre annulée",
    transaction_cancelled: "Transaction annulée",
    currency_created: "Monnaie créée",
    currency_changed: "Monnaie modifiée",
    currency_deleted: "Monnaie supprimée",
    currency_faction_added: "Faction ajoutée à une monnaie",
    currency_faction_removed: "Faction retirée d'une monnaie",
    currency_issuer_changed: "Émetteur de monnaie changé",
};

export const GLOBAL_ROLE_LABELS: Record<string, string> = {
    admin: "Admin",
    train_admin: "Admin trains",
    money_admin: "Admin monnaies",
};

/** The server-wide roles an admin can hand out. */
export const GLOBAL_ROLES = ["admin", "train_admin", "money_admin"] as const;

export const TARGET_LABELS: Record<string, string> = {
    user: "Compte",
    faction: "Faction",
    train: "Train",
    line: "Ligne",
    station: "Gare",
    territory: "Territoire",
    marker: "Point de carte",
    offer: "Offre",
    transaction: "Transaction",
    currency: "Monnaie",
};

/**
 * Ask an admin why they cancel something; null when they give up. The server
 * wants at least 3 characters and tells the people concerned.
 */
export function askReason(question: string): string | null {
    const reason = window.prompt(`${question}\n\nMotif (obligatoire) :`);
    if (reason === null) return null;
    if (reason.trim().length < 3) {
        window.alert("Un motif d'au moins 3 caractères est obligatoire.");
        return null;
    }
    return reason.trim().slice(0, 200);
}

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
        case "offer":
            return `/offers`;
        case "territory":
        case "marker":
            return `/actual`;
        default:
            return null;
    }
}
