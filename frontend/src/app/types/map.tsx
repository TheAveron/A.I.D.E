export const MARKER_KINDS = {
    city: "Ville / Projet",
    station: "Gare",
    trial_chamber: "Trial chamber",
    village: "Village",
    ocean_monument: "Ocean monument",
    ancient_city: "Ancient city",
    stronghold: "Stronghold",
    nether_bastion: "Bastion du Nether",
    nether_fortress: "Forteresse du Nether",
    end_city: "Cité de l'End",
    spawn: "Spawn",
    generic: "Point d'intérêt",
} as const;

export type MarkerKind = keyof typeof MARKER_KINDS;

export interface TerritoryType {
    territory_id: number;
    map_name: string;
    name: string;
    description: string | null;
    color: string | null;
    faction_id: number;
    faction_name: string | null;
    /** [x, z] in blocks, the ring is stored open. */
    points: [number, number][];
    created_at: string;
    updated_at: string;
}

export interface MarkerType {
    marker_id: number;
    map_name: string;
    label: string;
    description: string | null;
    kind: MarkerKind;
    x: number;
    z: number;
    faction_id: number | null;
    user_id: number | null;
    owner_name: string | null;
    created_at: string;
}

/** The dimension a map folder shows: its first letter (see utils/maps.ts). */
export function dimensionOfFolder(
    folder: string,
): "overworld" | "nether" | "end" {
    if (folder.startsWith("N")) return "nether";
    if (folder.startsWith("E")) return "end";
    return "overworld";
}
