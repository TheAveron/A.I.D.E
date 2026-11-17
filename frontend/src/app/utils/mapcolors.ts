const PALETTE = [
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

/** "#rrggbb" and an opacity as "rgba(...)". */
export function withAlpha(hex: string, alpha: number): string {
    const value = parseInt(hex.slice(1), 16);
    const r = (value >> 16) & 255;
    const g = (value >> 8) & 255;
    const b = value & 255;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
