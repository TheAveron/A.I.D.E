export type MarkerKind = "base" | "resource" | "portal" | "landmark" | "other";

export const MARKER_KINDS: Record<MarkerKind, string> = {
    base: "Base",
    resource: "Ressource",
    portal: "Portail",
    landmark: "Point de repère",
    other: "Autre",
};

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
