/**
 * What a uNmINeD export of a map contains, and how its tiles are laid out.
 *
 * The export (backend/documents/maps/<folder>) holds the tiles and three small
 * scripts written by uNmINeD: the map properties, the regions that have tiles
 * and the players. The geometry below is the one of uNmINeD's own viewer, so
 * every tile lands where it does there.
 */
import { boundingExtent, type Extent } from "ol/extent";
import Projection from "ol/proj/Projection";
import TileGrid from "ol/tilegrid/TileGrid";

export interface UnminedProperties {
    minZoom: number;
    maxZoom: number;
    defaultZoom: number;
    imageFormat: string;
    minRegionX: number;
    minRegionZ: number;
    maxRegionX: number;
    maxRegionZ: number;
    worldName: string;
    background: string;
    centerX: number;
    centerZ: number;
}

/** 32x32 regions: `m` holds one bit per region, 32 per number. */
export interface RegionGroup {
    x: number;
    z: number;
    m: number[];
}

export interface UnminedPlayer {
    name: string;
    x: number;
    z: number;
}

export interface UnminedData {
    properties: UnminedProperties;
    regions: RegionGroup[];
    players: UnminedPlayer[];
}

const TILE_SIZE = 256;

/**
 * Run an export's script and take the variable it defines. The script uses
 * `var`, a global that cannot be deleted: it is reset before the load and read
 * after it.
 */
function loadScript<T>(src: string, variable: string): Promise<T> {
    return new Promise((resolve, reject) => {
        const holder = window as unknown as Record<string, unknown>;
        // The previous map's value must not pass for this one's
        holder[variable] = undefined;
        const script = document.createElement("script");
        script.src = src;
        script.async = true;
        script.onload = () => {
            const value = holder[variable] as T | undefined;
            script.remove();
            if (value === undefined) reject(new Error(`${src}: ${variable}`));
            else resolve(value);
        };
        script.onerror = () => {
            script.remove();
            reject(new Error(`${src} unreachable`));
        };
        document.head.appendChild(script);
    });
}

// A script of uNmINeD declares its data with `var`, which makes it a global.
const FILES = {
    properties: ["unmined.map.properties.js", "UnminedMapProperties"],
    regions: ["unmined.map.regions.js", "UnminedRegions"],
    players: ["unmined.map.players.js", "UnminedPlayers"],
} as const;

export async function loadUnminedData(folder: string): Promise<UnminedData> {
    const base = `/maps/${encodeURIComponent(folder)}/`;
    // The three scripts define different variables, but load one after the
    // other anyway: each one is read and removed before the next starts.
    const properties = await loadScript<UnminedProperties>(
        base + FILES.properties[0],
        FILES.properties[1],
    );
    const regions = await loadScript<RegionGroup[]>(
        base + FILES.regions[0],
        FILES.regions[1],
    );
    let players: UnminedPlayer[] = [];
    try {
        const loaded = await loadScript<UnminedPlayer[]>(
            base + FILES.players[0],
            FILES.players[1],
        );
        if (Array.isArray(loaded)) players = loaded;
    } catch {
        // A map without players is still a map.
    }
    return { properties, regions, players };
}

export interface MapGeometry {
    projection: Projection;
    tileGrid: TileGrid;
    extent: Extent;
    resolutions: number[];
    zoomLevels: number;
    /** The zoom at which one pixel is one block. */
    defaultZoom: number;
    pixelRatio: number;
    /** Blocks (x, z) -> view coordinates, and back. */
    toView: (block: [number, number]) => [number, number];
    toBlocks: (view: number[]) => [number, number];
    /** Blocks covered by one view unit. */
    blocksPerUnit: number;
    tileUrl: (z: number, x: number, y: number) => string | undefined;
}

function hasTile(
    regions: RegionGroup[],
    bounds: { minX: number; minZ: number; width: number; height: number },
    tileX: number,
    tileZ: number,
    zoom: number,
): boolean {
    const zoomFactor = Math.pow(2, zoom);
    const minTileX = Math.floor((bounds.minX * zoomFactor) / TILE_SIZE);
    const minTileZ = Math.floor((bounds.minZ * zoomFactor) / TILE_SIZE);
    const maxTileX =
        Math.ceil(((bounds.minX + bounds.width) * zoomFactor) / TILE_SIZE) - 1;
    const maxTileZ =
        Math.ceil(((bounds.minZ + bounds.height) * zoomFactor) / TILE_SIZE) - 1;
    if (
        tileX < minTileX ||
        tileZ < minTileZ ||
        tileX > maxTileX ||
        tileZ > maxTileZ
    ) {
        return false;
    }

    const tileBlockSize = TILE_SIZE / zoomFactor;
    const firstRegionX = Math.floor((tileX * tileBlockSize) / 512);
    const firstRegionZ = Math.floor((tileZ * tileBlockSize) / 512);
    const regionCount = Math.ceil(tileBlockSize / 512);

    for (let x = firstRegionX; x < firstRegionX + regionCount; x++) {
        for (let z = firstRegionZ; z < firstRegionZ + regionCount; z++) {
            const gx = Math.floor(x / 32);
            const gz = Math.floor(z / 32);
            const group = regions.find((r) => r.x === gx && r.z === gz);
            if (!group) continue;
            const index = (z - gz * 32) * 32 + (x - gx * 32);
            const word = group.m[Math.floor(index / 32)];
            if ((word & (1 << (index % 32))) !== 0) return true;
        }
    }
    return false;
}

export function buildGeometry(
    folder: string,
    properties: UnminedProperties,
    regions: RegionGroup[],
    pixelRatio = window.devicePixelRatio || 1,
): MapGeometry {
    const bounds = {
        minX: properties.minRegionX * 512,
        minZ: properties.minRegionZ * 512,
        width: (properties.maxRegionX + 1 - properties.minRegionX) * 512,
        height: (properties.maxRegionZ + 1 - properties.minRegionZ) * 512,
    };
    const farthest = Math.max(
        Math.abs(bounds.minX),
        Math.abs(bounds.minZ),
        Math.abs(bounds.minX + bounds.width),
        Math.abs(bounds.minZ + bounds.height),
    );
    // The view is a square of 540 units whatever the size of the world
    const blocksPerUnit = Math.max(30000000, farthest) / 270;

    const toView = ([x, z]: [number, number]): [number, number] => [
        x / blocksPerUnit,
        -z / blocksPerUnit,
    ];
    const toBlocks = (view: number[]): [number, number] => [
        view[0] * blocksPerUnit,
        -view[1] * blocksPerUnit,
    ];

    const projection = new Projection({
        code: "UNMINED-VIEW",
        units: "pixels",
        extent: [-270, -270, 270, 270],
    });

    const extent = boundingExtent([
        toView([bounds.minX, bounds.minZ]),
        toView([bounds.minX + bounds.width, bounds.minZ + bounds.height]),
    ]);

    const zoomLevels = properties.maxZoom - properties.minZoom;
    const resolutions: number[] = [];
    for (let z = 0; z <= zoomLevels; z++) {
        const blocks = Math.pow(2, zoomLevels - z - properties.maxZoom);
        resolutions.push((blocks / blocksPerUnit) * pixelRatio);
    }

    const tileGrid = new TileGrid({
        extent,
        origin: [0, 0],
        resolutions,
        tileSize: TILE_SIZE / pixelRatio,
    });

    const tileUrl = (z: number, x: number, y: number) => {
        const worldZoom = properties.maxZoom - (zoomLevels - z);
        if (!hasTile(regions, bounds, x, y, worldZoom)) return undefined;
        return (
            `/maps/${encodeURIComponent(folder)}/tiles/zoom.${worldZoom}/` +
            `${Math.floor(x / 10)}/${Math.floor(y / 10)}/tile.${x}.${y}.` +
            properties.imageFormat
        );
    };

    return {
        projection,
        tileGrid,
        extent,
        resolutions,
        zoomLevels,
        defaultZoom: zoomLevels - properties.maxZoom,
        pixelRatio,
        toView,
        toBlocks,
        blocksPerUnit,
        tileUrl,
    };
}
