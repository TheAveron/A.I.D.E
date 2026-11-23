import axios from "axios";

// Same limits as the server (app/crud/schematic.py, app/schemas/schematic.py)
export const MAX_NBT_BYTES = 5 * 1024 * 1024;
export const MAX_PREVIEW_BYTES = 2 * 1024 * 1024;
export const TITLE_MAX = 100;
export const COMMENT_MAX = 500;
export const MAX_TAGS = 10;
export const TAG_MAX = 30;

/** Tags proposed before anybody has used one. */
export const DEFAULT_TAGS = [
    "train",
    "voyageurs",
    "fret",
    "fluides",
    "gare",
    "intersection",
    "voie",
    "tunnel",
    "pont",
    "usine",
    "ferme",
    "maison",
    "décor",
];

/** "  Train  de FRET " -> "train de fret" (like the server). */
export function cleanTag(value: string): string {
    return value.normalize("NFC").replace(/\s+/g, " ").trim().toLowerCase();
}

export function isValidTag(tag: string): boolean {
    return tag.length > 0 && tag.length <= TAG_MAX && /^[\p{L}\p{N} -]+$/u.test(tag);
}

export function formatBytes(bytes: number): string {
    if (bytes < 1024) return `${bytes} o`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
}

export function formatSize(v: { size_x: number; size_y: number; size_z: number }) {
    return `${v.size_x} × ${v.size_y} × ${v.size_z}`;
}

/** The file name the server gives in Content-Disposition, if any. */
function fileNameOf(disposition: string | undefined, fallback: string): string {
    if (!disposition) return fallback;
    const encoded = /filename\*=utf-8''([^;]+)/i.exec(disposition);
    if (encoded) {
        try {
            return decodeURIComponent(encoded[1]);
        } catch {
            /* fall through */
        }
    }
    const plain = /filename="?([^";]+)"?/i.exec(disposition);
    return plain ? plain[1] : fallback;
}

/** Download a version: the API needs the token, so no plain link. */
export async function downloadVersion(schematicId: number, number: number) {
    const res = await axios.get<Blob>(
        `/schematics/${schematicId}/versions/${number}/download`,
        { responseType: "blob" },
    );
    const name = fileNameOf(
        res.headers["content-disposition"] as string | undefined,
        `schematic-v${number}.nbt`,
    );
    const url = URL.createObjectURL(res.data);
    const link = document.createElement("a");
    link.href = url;
    link.download = name;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}

const IMAGE_TYPES = ["image/png", "image/jpeg", "image/webp"];

/** What is wrong with the chosen .nbt file, or "" (the server checks again). */
export function nbtProblem(file: File | null): string {
    if (!file) return "Choisissez un fichier .nbt.";
    if (!file.name.toLowerCase().endsWith(".nbt")) {
        return "Seuls les fichiers .nbt sont acceptés.";
    }
    if (file.size > MAX_NBT_BYTES) {
        return `Le fichier dépasse ${formatBytes(MAX_NBT_BYTES)}.`;
    }
    return "";
}

export function previewProblem(file: File | null): string {
    if (!file) return "";
    if (!IMAGE_TYPES.includes(file.type)) {
        return "L'aperçu doit être une image PNG, JPEG ou WebP.";
    }
    if (file.size > MAX_PREVIEW_BYTES) {
        return `L'aperçu dépasse ${formatBytes(MAX_PREVIEW_BYTES)}.`;
    }
    return "";
}
