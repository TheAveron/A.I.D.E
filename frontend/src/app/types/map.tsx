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

/** Generated structures: their loot can be marked as taken ("explored"). */
export const STRUCTURE_KINDS: ReadonlySet<MarkerKind> = new Set<MarkerKind>([
    "trial_chamber",
    "village",
    "ocean_monument",
    "ancient_city",
    "stronghold",
    "nether_bastion",
    "nether_fortress",
    "end_city",
]);

export function isStructure(kind: MarkerKind): boolean {
    return STRUCTURE_KINDS.has(kind);
}

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
    /** For a structure: its valuable loot was already taken. */
    explored: boolean;
    explored_by_name: string | null;
    explored_at: string | null;
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
