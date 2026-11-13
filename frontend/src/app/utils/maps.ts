/**
 * The maps of the archives: one folder per map in backend/documents/maps
 * (first letter: O overworld, E end, N nether). To add a map, add its folder
 * to MAP_LABELS - this is the only place - and to LISTED_MAPS if it should
 * appear in the archives list.
 */
export const MAP_LABELS: Record<string, string> = {
    OAOS_zoom: "Cube Crusader: Age of Steam",
    OCube_crusader: "Cube Crusader: The Origin",
    OLSLN: "La survie pour les nuls",
    OLSPLW_zoom: "La survie pour les Wariors",
    OStrong_world_zoom: "Strong World",
    OSurvival_islands_zoom: "Survival Islands",
    OUtopia_zoom: "Utopia",
    EUtopia_zoom: "End d'Utopia",
};

// The Age of Steam map is the current server's one ("/actual"), not archived.
const CURRENT_MAP = "OAOS_zoom";

export const LISTED_MAPS = Object.keys(MAP_LABELS).filter(
    (folder) => folder !== CURRENT_MAP,
);

export const CURRENT_MAP_FOLDER = CURRENT_MAP;

export function getLabelFromFolder(folder: string): string {
    return MAP_LABELS[folder] ?? folder;
}
