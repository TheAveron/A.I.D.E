export const PALETTE = [
    "#e6194b",
    "#3cb44b",
    "#4363d8",
    "#f58231",
    "#911eb4",
    "#42d4f4",
    "#f032e6",
    "#bfef45",
    "#fabed4",
    "#469990",
    "#dcbeff",
    "#9a6324",
];

/** The colour of a faction's territories when none was chosen: stable per faction. */
export function factionColor(factionId: number, chosen?: string | null) {
    if (chosen && /^#[0-9a-fA-F]{6}$/.test(chosen)) return chosen;
    return PALETTE[Math.abs(factionId) % PALETTE.length];
}

/** A territory's colour: the chosen one, else its faction's, else one
 *  stable per player (shifted so it differs from the faction of same id). */
export function territoryColor(t: {
    faction_id: number | null;
    user_id: number | null;
    color: string | null;
}): string {
    return t.faction_id !== null
        ? factionColor(t.faction_id, t.color)
        : factionColor((t.user_id ?? 0) + 5, t.color);
}

/** "#rrggbb" and an opacity as "rgba(...)". */
export function withAlpha(hex: string, alpha: number): string {
    const value = parseInt(hex.slice(1), 16);
    const r = (value >> 16) & 255;
    const g = (value >> 8) & 255;
    const b = value & 255;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/** The dot of a generic point when no colour was chosen (generic.svg). */
export const DEFAULT_POINT_COLOR = "#ffb300";

/** "#a1B2c3" or "a1B2c3" as "#a1b2c3"; null when it is not a colour. */
export function normalizeHex(value: string): string | null {
    const match = /^#?([0-9a-fA-F]{6})$/.exec(value.trim());
    return match ? `#${match[1].toLowerCase()}` : null;
}
