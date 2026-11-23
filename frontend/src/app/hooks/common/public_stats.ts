import { usePublicGet } from "../network/map";

export interface PublicStats {
    // Accounts, the admins' left out
    members: number;
    // Towns and projects placed on the maps
    projects: number;
    factions: number;
}

/** Figures about the server shown on the home page (no account needed). */
export function usePublicStats() {
    const { data } = usePublicGet<PublicStats>(
        "/stats",
        "Erreur lors du chargement des chiffres",
    );
    return data;
}
