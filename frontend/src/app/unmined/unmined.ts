import Map from "ol/Map";
import View from "ol/View";
import Projection from "ol/proj/Projection";
import { transform, transformExtent, addCoordinateTransforms } from "ol/proj";
import { boundingExtent } from "ol/extent";
import TileGrid from "ol/tilegrid/TileGrid";
import TileLayer from "ol/layer/Tile";
import VectorLayer from "ol/layer/Vector";
import XYZ from "ol/source/XYZ";
import VectorSource from "ol/source/Vector";
import MousePosition from "ol/control/MousePosition";
import ScaleLine from "ol/control/ScaleLine";
import { createStringXY } from "ol/coordinate";
import Feature from "ol/Feature";
import Point from "ol/geom/Point";
import Style from "ol/style/Style";
import Icon from "ol/style/Icon";
import CircleStyle from "ol/style/Circle";
import Fill from "ol/style/Fill";
import Stroke from "ol/style/Stroke";
import Text from "ol/style/Text";
import Graticule from "ol/layer/Graticule";
import Toastify from "react-toastify";
import ContextMenu from "ol-contextmenu";

import type { Marker } from "./custom.markers";

// ======================
// RegionMap
// ======================
export class RegionMap {
    constructor(
        private regionMap: any[],
        private tileSize: number,
        private worldMinX: number,
        private worldMinZ: number,
        private worldWidth: number,
        private worldHeight: number
    ) {}

    hasTile(tileX: number, tileZ: number, unminedZoomLevel: number): boolean {
        const zoomFactor = Math.pow(2, unminedZoomLevel);

        const minTileX = Math.floor(
            (this.worldMinX * zoomFactor) / this.tileSize
        );
        const minTileZ = Math.floor(
            (this.worldMinZ * zoomFactor) / this.tileSize
        );
        const maxTileX =
            Math.ceil(
                ((this.worldMinX + this.worldWidth) * zoomFactor) /
                    this.tileSize
            ) - 1;
        const maxTileZ =
            Math.ceil(
                ((this.worldMinZ + this.worldHeight) * zoomFactor) /
                    this.tileSize
            ) - 1;

        if (
            tileX < minTileX ||
            tileZ < minTileZ ||
            tileX > maxTileX ||
            tileZ > maxTileZ
        ) {
            return false;
        }

        const tileBlockSize = this.tileSize / zoomFactor;
        const tileBlockPoint = {
            x: tileX * tileBlockSize,
            z: tileZ * tileBlockSize,
        };

        const tileRegionPoint = {
            x: Math.floor(tileBlockPoint.x / 512),
            z: Math.floor(tileBlockPoint.z / 512),
        };
        const tileRegionSize = Math.ceil(tileBlockSize / 512);

        for (
            let x = tileRegionPoint.x;
            x < tileRegionPoint.x + tileRegionSize;
            x++
        ) {
            for (
                let z = tileRegionPoint.z;
                z < tileRegionPoint.z + tileRegionSize;
                z++
            ) {
                const group = {
                    x: Math.floor(x / 32),
                    z: Math.floor(z / 32),
                };
                const regionMap = this.regionMap.find(
                    (e) => e.x == group.x && e.z == group.z
                );
                if (regionMap) {
                    const relX = x - group.x * 32;
                    const relZ = z - group.z * 32;
                    const inx = relZ * 32 + relX;
                    var b = regionMap.m[Math.floor(inx / 32)];
                    var bit = inx % 32;
                    var found = (b & (1 << bit)) != 0;
                    if (found) return true;
                }
            }
        }
        return false;
    }
}

// ======================
// RedDotMarker
// ======================
export class RedDotMarker {
    private source: VectorSource;
    private layer: VectorLayer<VectorSource>;
    private map: Map;
    private dataProjection: Projection;
    private viewProjection: Projection;

    constructor(
        map: Map,
        dataProjection: Projection,
        viewProjection: Projection
    ) {
        this.map = map;
        this.dataProjection = dataProjection;
        this.viewProjection = viewProjection;

        this.source = new VectorSource({ features: [] });
        this.layer = new VectorLayer({
            source: this.source,
            zIndex: 1000,
        });

        this.map.addLayer(this.layer);

        window.addEventListener("hashchange", (e: HashChangeEvent) => {
            this.hashChanged((e as any).newURL);
        });
        this.hashChanged(window.location.href);
    }

    getCoordinates(): [number, number] | undefined {
        return RedDotMarker.getCoordinatesFromUrlHash(window.location.hash);
    }

    static getCoordinatesFromUrlHash(
        hash: string
    ): [number, number] | undefined {
        if (!hash || hash.length <= 1) return undefined;

        const q = new URLSearchParams(hash.substring(1));
        const rx = q.get("rx");
        const rz = q.get("rz");
        if (!rx || !rz) return undefined;

        return [parseInt(rx), parseInt(rz)];
    }

    static getUrlHashWithCoordinates(
        hash: string | undefined,
        coordinates?: [number, number]
    ): string {
        hash ??= "#";
        const q = new URLSearchParams(hash.substring(1));
        if (!coordinates) {
            q.delete("rx");
            q.delete("rz");
        } else {
            q.set("rx", coordinates[0].toString());
            q.set("rz", coordinates[1].toString());
        }
        return "#" + q.toString();
    }

    setCoordinates(coordinates?: [number, number]) {
        const url = new URL(window.location.href);
        url.hash = RedDotMarker.getUrlHashWithCoordinates(
            url.hash,
            coordinates
        );
        window.location.replace(url);
    }

    private hashChanged(newURL: string) {
        const c = RedDotMarker.getCoordinatesFromUrlHash(new URL(newURL).hash);
        this.setRedDotMarker(c);
    }

    private setRedDotMarker(coordinates?: [number, number]) {
        this.source.clear();
        if (!coordinates) return;

        const marker = new Feature({
            geometry: new Point(
                transform(coordinates, this.dataProjection, this.viewProjection)
            ),
        });

        marker.setStyle(
            new Style({
                image: new CircleStyle({
                    radius: 6,
                    fill: new Fill({ color: "red" }),
                    stroke: new Stroke({ color: "#ffffff", width: 2 }),
                }),
                text: new Text({
                    text: `${coordinates[0]}, ${coordinates[1]}`,
                    font: "bold 14px Arial",
                    offsetY: 25,
                    fill: new Fill({ color: "#000000" }),
                    stroke: new Stroke({ color: "#ffffff", width: 3 }),
                    padding: [4, 6, 4, 6],
                }),
            })
        );

        this.source.addFeature(marker);
    }
}

// ======================
// Unmined main class
// ======================
export interface UnminedMapProperties {
    worldName: string;
    tileSize: number;
    markers: Marker[];
    playerMarkers?: Marker[];
    zoomLevels: number;
    // Any other properties from unmined.map.properties.js
    [key: string]: any;
}

export class Unmined {
    private map: Map;
    private viewProjection: Projection;
    private dataProjection: Projection;
    private regionMap: RegionMap;
    private redDot: RedDotMarker;

    constructor(
        container: HTMLElement,
        private properties: UnminedMapProperties,
        private regions: any[]
    ) {
        // Create projections
        this.dataProjection = new Projection({
            code: "UNMINED",
            units: "pixels",
            extent: [0, 0, properties.worldWidth, properties.worldHeight],
        });

        this.viewProjection = new Projection({
            code: "VIEW",
            units: "pixels",
            extent: [0, 0, properties.worldWidth, properties.worldHeight],
        });

        addCoordinateTransforms(
            this.dataProjection,
            this.viewProjection,
            (coord) => coord,
            (coord) => coord
        );

        // Region map
        this.regionMap = new RegionMap(
            regions,
            properties.tileSize,
            properties.worldMinX,
            properties.worldMinZ,
            properties.worldWidth,
            properties.worldHeight
        );

        // Map view
        const view = new View({
            projection: this.viewProjection,
            center: [properties.worldWidth / 2, properties.worldHeight / 2],
            zoom: 0,
            maxZoom: properties.zoomLevels - 1,
        });

        // Base tile layer
        const tileGrid = new TileGrid({
            origin: [0, 0],
            tileSize: properties.tileSize,
            resolutions: Array.from({ length: properties.zoomLevels }, (_, z) =>
                Math.pow(2, properties.zoomLevels - 1 - z)
            ),
        });

        const tileLayer = new TileLayer({
            source: new XYZ({
                projection: this.viewProjection,
                tileGrid,
                tileUrlFunction: (tileCoord) => {
                    const [z, x, y] = tileCoord;
                    if (!this.regionMap.hasTile(x, y, z)) {
                        return "";
                    }
                    return `tiles/${z}/${x}_${y}.png`;
                },
            }),
        });

        // Marker layer
        const markerSource = new VectorSource();
        const markerLayer = new VectorLayer({
            source: markerSource,
        });

        // Add default markers
        this.addMarkers(markerSource, properties.markers);
        if (properties.playerMarkers) {
            this.addMarkers(markerSource, properties.playerMarkers);
        }

        // Create map
        this.map = new Map({
            target: container,
            layers: [tileLayer, markerLayer],
            view,
            controls: [
                new MousePosition({
                    coordinateFormat: createStringXY(0),
                    projection: this.dataProjection,
                }),
                new ScaleLine(),
            ],
        });

        // Red dot
        this.redDot = new RedDotMarker(
            this.map,
            this.dataProjection,
            this.viewProjection
        );

        // Context menu
        this.addContextMenu();
    }

    private addMarkers(source: VectorSource, markers: Marker[]) {
        markers.forEach((m) => {
            const feature = new Feature({
                geometry: new Point(
                    transform(
                        [m.x, m.z],
                        this.dataProjection,
                        this.viewProjection
                    )
                ),
            });

            feature.setStyle(
                new Style({
                    image: m.image
                        ? new Icon({
                              src: m.image,
                              anchor: m.imageAnchor ?? [0.5, 1],
                              scale: m.imageScale ?? 1,
                          })
                        : undefined,
                    text: m.text
                        ? new Text({
                              text: m.text,
                              font: m.font ?? "bold 14px Arial",
                              fill: new Fill({ color: m.textColor ?? "black" }),
                              offsetX: m.offsetX ?? 0,
                              offsetY: m.offsetY ?? 0,
                          })
                        : undefined,
                })
            );

            source.addFeature(feature);
        });
    }

    private addContextMenu() {
        const contextmenu = new ContextMenu({
            width: 170,
            defaultItems: true,
            items: [
                {
                    text: "Set Red Dot",
                    callback: (obj: any) => {
                        const coords = transform(
                            obj.coordinate,
                            this.viewProjection,
                            this.dataProjection
                        );
                        this.redDot.setCoordinates([coords[0], coords[1]]);
                        Toastify({
                            text: `Red dot set at ${coords[0]}, ${coords[1]}`,
                            duration: 2000,
                        }).showToast();
                    },
                },
                {
                    text: "Clear Red Dot",
                    callback: () => {
                        this.redDot.setCoordinates(undefined);
                        Toastify({
                            text: "Red dot cleared",
                            duration: 2000,
                        }).showToast();
                    },
                },
            ],
        });
        this.map.addControl(contextmenu);
    }
}
