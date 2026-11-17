import type { MarkerKind } from "../types/map";

// One image (PNG or SVG) per kind in assets/images/map, named after the kind:
// replacing a file changes the icon everywhere, adding a kind is adding its
// file. The pictures are pixel art, drawn crisp by the browser where shown.
const FILES = import.meta.glob("../../assets/images/map/*.{png,svg}", {
    eager: true,
    query: "?url",
    import: "default",
}) as Record<string, string>;

const BY_KIND = new Map<string, string>(
    Object.entries(FILES).map(([path, url]) => [
        path
            .split("/")
            .pop()!
            .replace(/\.(png|svg)$/, ""),
        url,
    ]),
);

export function iconUrl(kind: MarkerKind): string {
    return BY_KIND.get(kind) ?? BY_KIND.get("generic") ?? "";
}
