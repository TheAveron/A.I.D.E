import type { TrainService } from "../types/trains";

export const MAINTENANCE_LINE = "Z";
export const COMMON_NAME_MAX = 24;

export const SERVICES: Record<TrainService, string> = {
    O: "Omnibus : toutes les gares de la ligne",
    E: "Express : les deux extrémités seulement",
    F: "Fret",
    L: "Liquide",
};

export const SERVICE_NAMES: Record<TrainService, string> = {
    O: "Omnibus",
    E: "Express",
    F: "Fret",
    L: "Liquide",
};

/** A to Y, optionally followed by 1-9 (a branch); Z is maintenance. */
export function isLineCode(code: string): boolean {
    return /^([A-Y][1-9]?|Z)$/.test(code);
}

/**
 * The name shown in stations, as the server will build it. `number` is the
 * one the server is expected to attribute: null before it is known.
 */
export function previewTrainName(
    line: string,
    service: TrainService | "",
    number: number | null,
    commonName: string,
): string {
    const digits = number === null ? "00" : String(number).padStart(2, "0");
    const base = `${line || "L"}-${line === MAINTENANCE_LINE ? "" : service || "S"}${digits}`;
    const name = commonName.trim();
    return name ? `${base} ${name}` : base;
}

/** The first number from 1 to 99 not in `used`, or null when all are taken. */
export function firstFreeNumber(used: Iterable<number>): number | null {
    const taken = new Set(used);
    for (let n = 1; n <= 99; n++) {
        if (!taken.has(n)) return n;
    }
    return null;
}

/**
 * One platform per line, "name : description" (the description is optional):
 * `1 : vers le nord, de plain-pied` becomes {name: "1", description: ...}.
 */
export function parsePlatforms(
    text: string,
): { name: string; description: string | null }[] {
    return text
        .split("\n")
        .map((row) => row.trim())
        .filter((row) => row !== "")
        .map((row) => {
            const cut = row.indexOf(":");
            if (cut === -1) return { name: row, description: null };
            return {
                name: row.slice(0, cut).trim(),
                description: row.slice(cut + 1).trim() || null,
            };
        });
}

/** Whole-number coordinate from an input; null when empty or not a whole number. */
export function parseCoordinate(text: string): number | null {
    const value = text.trim();
    return /^-?\d+$/.test(value) ? Number(value) : null;
}
