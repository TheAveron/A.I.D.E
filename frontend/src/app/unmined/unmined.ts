import ol from "ol";
import { Map, Feature, View } from "ol";
import { Vector as VectorLayer, Tile as TileLayer, Graticule } from "ol/layer";
import { Vector as VectorSource, XYZ } from "ol/source";
import { Point } from "ol/geom";
import {
    Style,
    Icon,
    Text,
    Fill,
    Stroke,
    Circle as CircleStyle,
} from "ol/style";
import { MousePosition, ScaleLine } from "ol/control";
import { Projection } from "ol/proj";
import TileGrid from "ol/tilegrid/TileGrid";

// Type definitions for external libraries
declare const Toastify: any;
declare const ContextMenu: any;

interface RegionMapData {
    x: number;
    z: number;
    m: number[];
}

interface Point2D {
    x: number;
    z: number;
}

interface Coordinates {
    x: number;
    z: number;
}

interface MarkerItem {
    x: number;
    z: number;
    image?: string;
    imageAnchor?: [number, number];
    imageScale?: number;
    text?: string;
    font?: string;
    offsetX?: number;
    offsetY?: number;
    textColor?: string;
    textPadding?: [number, number, number, number];
    textStrokeColor?: string;
    textStrokeWidth?: number;
    textBackgroundColor?: string;
    textBackgroundStrokeColor?: string;
    textBackgroundStrokeWidth?: number;
}

interface Player {
    x: number;
    z: number;
    name: string;
}

interface UnminedOptions {
    enableGrid?: boolean;
    showGrid?: boolean;
    binaryGrid?: boolean;
    showScaleBar?: boolean;
    denseGrid?: boolean;
    showMarkers?: boolean;
    showPlayers?: boolean;
    centerX?: number;
    centerZ?: number;
    minRegionX: number;
    minRegionZ: number;
    maxRegionX: number;
    maxRegionZ: number;
    minZoom: number;
    maxZoom: number;
    imageFormat: string;
    markers?: MarkerItem[];
    playerMarkers?: MarkerItem[];
    background?: string;
}

interface MapSettings {
    showScaleBar: boolean;
    showGrid: boolean;
    binaryGrid: boolean;
    denseGrid: boolean;
    showMarkers: boolean;
    showPlayers: boolean;
}

class RegionMap {
    private regionMap: RegionMapData[];
    private tileSize: number;
    private worldMinX: number;
    private worldMinZ: number;
    private worldWidth: number;
    private worldHeight: number;

    constructor(
        regionMap: RegionMapData[],
        tileSize: number,
        worldMinX: number,
        worldMinZ: number,
        worldWidth: number,
        worldHeight: number
    ) {
        this.regionMap = regionMap;
        this.tileSize = tileSize;
        this.worldMinX = worldMinX;
        this.worldMinZ = worldMinZ;
        this.worldWidth = worldWidth;
        this.worldHeight = worldHeight;
    }

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
        const tileBlockPoint: Point2D = {
            x: tileX * tileBlockSize,
            z: tileZ * tileBlockSize,
        };

        const tileRegionPoint: Point2D = {
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
                const group: Point2D = {
                    x: Math.floor(x / 32),
                    z: Math.floor(z / 32),
                };
                const regionMap = this.regionMap.find(
                    (e) => e.x === group.x && e.z === group.z
                );
                if (regionMap) {
                    const relX = x - group.x * 32;
                    const relZ = z - group.z * 32;
                    const inx = relZ * 32 + relX;
                    const b = regionMap.m[Math.floor(inx / 32)];
                    const bit = inx % 32;
                    const found = (b & (1 << bit)) !== 0;
                    if (found) return true;
                }
            }
        }
        return false;
    }
}

class RedDotMarker {
    private source: VectorSource | undefined = undefined;
    private layer: VectorLayer<VectorSource> | undefined = undefined;
    private map: Map | undefined = undefined;
    private dataProjection: Projection | undefined = undefined;
    private viewProjection: Projection | undefined = undefined;

    constructor(
        map: Map,
        dataProjection: Projection,
        viewProjection: Projection
    ) {
        this.map = map;
        this.dataProjection = dataProjection;
        this.viewProjection = viewProjection;

        this.source = new VectorSource({
            features: [],
        });
        this.layer = new VectorLayer({
            source: this.source,
            zIndex: 1000,
        });

        this.map.addLayer(this.layer);

        window.addEventListener("hashchange", (e: HashChangeEvent) => {
            this.hashChanged(e.newURL);
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

        const c: [number, number] = [parseInt(rx), parseInt(rz)];
        return c;
    }

    static getUrlHashWithCoordinates(
        hash: string,
        coordinates?: [number, number]
    ): string {
        hash = hash ?? "#";
        const q = new URLSearchParams(hash.substring(1));
        if (!coordinates) {
            q.delete("rx");
            q.delete("rz");
        } else {
            q.set("rx", coordinates[0].toString());
            q.set("rz", coordinates[1].toString());
        }
        const s = q.toString();
        return "#" + s;
    }

    setCoordinates(coordinates?: [number, number]): void {
        const url = new URL(window.location.href);
        url.hash = RedDotMarker.getUrlHashWithCoordinates(
            url.hash,
            coordinates
        );
        window.location.replace(url);
    }

    private hashChanged(newURL: string): void {
        const c = RedDotMarker.getCoordinatesFromUrlHash(new URL(newURL).hash);
        this.setRedDotMarker(c);
    }

    private setRedDotMarker(coordinates?: [number, number]): void {
        this.source!.clear();

        if (!coordinates) return;

        const marker = new Feature({
            geometry: new Point(
                ol.proj.transform(
                    coordinates,
                    this.dataProjection!,
                    this.viewProjection!
                )
            ),
        });

        marker.setStyle(
            new Style({
                image: new CircleStyle({
                    radius: 6,
                    fill: new Fill({
                        color: "red",
                    }),
                    stroke: new Stroke({
                        color: "#ffffff",
                        width: 2,
                    }),
                }),
                text: new Text({
                    text: coordinates[0] + ", " + coordinates[1],
                    font: "bold 14px Arial",
                    offsetY: 25,
                    fill: new Fill({ color: "#000000" }),
                    stroke: new Stroke({
                        color: "#ffffff",
                        width: 3,
                    }),
                    padding: [4, 6, 4, 6],
                }),
            })
        );

        this.source!.addFeature(marker);
    }
}

class Unmined {
    olMap: Map | null = null;
    gridLayer: Graticule | null = null;
    coordinateLayer: Graticule | null = null;
    viewProjection: Projection | null = null;
    dataProjection: Projection | null = null;
    regionMap: RegionMap | null = null;
    markersLayer: VectorLayer<VectorSource> | null = null;
    playerMarkersLayer: VectorLayer<VectorSource> | null = null;
    redDotMarker!: RedDotMarker;

    private scaleLine: ScaleLine | null = null;
    private options: UnminedOptions;

    static defaultOptions: Partial<UnminedOptions> = {
        enableGrid: true,
        showGrid: true,
        binaryGrid: true,
        showScaleBar: true,
        denseGrid: false,
        showMarkers: true,
        showPlayers: true,
        centerX: 0,
        centerZ: 0,
    };

    constructor(
        mapElement: HTMLElement | string,
        options: UnminedOptions,
        regions: RegionMapData[]
    ) {
        const worldTileSize = 256;

        this.options = {
            ...Unmined.defaultOptions,
            ...options,
        } as UnminedOptions;

        this.loadSettings();

        const worldMinX = this.options.minRegionX * 512;
        const worldMinZ = this.options.minRegionZ * 512;
        const worldWidth =
            (this.options.maxRegionX + 1 - this.options.minRegionX) * 512;
        const worldHeight =
            (this.options.maxRegionZ + 1 - this.options.minRegionZ) * 512;

        this.regionMap = new RegionMap(
            regions,
            worldTileSize,
            worldMinX,
            worldMinZ,
            worldWidth,
            worldHeight
        );

        const dpiScale = window.devicePixelRatio ?? 1.0;

        this.initProjections(
            Math.max(
                Math.abs(worldMinX),
                Math.abs(worldMinZ),
                Math.abs(worldMinX + worldWidth),
                Math.abs(worldMinX + worldHeight)
            )
        );

        const mapExtent = ol.proj.transformExtent(
            ol.extent.boundingExtent([
                [worldMinX, worldMinZ],
                [worldMinX + worldWidth, worldMinZ + worldHeight],
            ]),
            this.dataProjection!,
            this.viewProjection!
        );

        const mapZoomLevels = this.options.maxZoom - this.options.minZoom;
        const resolutions = new Array(mapZoomLevels + 1);
        for (let z = 0; z <= mapZoomLevels; ++z) {
            let b = 1 * Math.pow(2, mapZoomLevels - z - this.options.maxZoom);
            b = ol.proj.transform(
                [b, b],
                this.dataProjection!,
                this.viewProjection!
            )[0];
            resolutions[z] = b * dpiScale;
        }

        const tileGrid = new TileGrid({
            extent: mapExtent,
            origin: [0, 0],
            resolutions: resolutions,
            tileSize: worldTileSize / dpiScale,
        });

        const unminedLayer = new TileLayer({
            source: new XYZ({
                projection: this.viewProjection!,
                tileGrid: tileGrid,
                tilePixelRatio: dpiScale,
                tileSize: worldTileSize / dpiScale,
                tileUrlFunction: (coordinate: number[]) => {
                    const tileX = coordinate[1];
                    const tileY = coordinate[2];

                    const worldZoom =
                        -(mapZoomLevels - coordinate[0]) + this.options.maxZoom;

                    if (this.regionMap!.hasTile(tileX, tileY, worldZoom)) {
                        const url = (
                            "tiles/zoom.{z}/{xd}/{yd}/tile.{x}.{y}." +
                            this.options.imageFormat
                        )
                            .replace("{z}", worldZoom.toString())
                            .replace("{yd}", Math.floor(tileY / 10).toString())
                            .replace("{xd}", Math.floor(tileX / 10).toString())
                            .replace("{y}", tileY.toString())
                            .replace("{x}", tileX.toString());
                        return url;
                    } else {
                        return undefined;
                    }
                },
            }),
        });

        const mousePositionControl = new MousePosition({
            coordinateFormat: ol.coordinate.createStringXY(0),
            projection: this.dataProjection!,
        });

        const map = new Map({
            target: mapElement,
            controls: ol.control.defaults
                .defaults()
                .extend([mousePositionControl]),
            layers: [unminedLayer],
            view: new View({
                center: ol.proj.transform(
                    [this.options.centerX!, this.options.centerZ!],
                    this.dataProjection!,
                    this.viewProjection!
                ),
                extent: mapExtent,
                projection: this.viewProjection!,
                resolutions: tileGrid.getResolutions(),
                maxZoom: mapZoomLevels,
                zoom: mapZoomLevels - this.options.maxZoom,
                constrainResolution: true,
                showFullExtent: true,
                constrainOnlyCenter: true,
                enableRotation: false,
            }),
        });

        if (this.options.markers && this.options.markers.length > 0) {
            this.markersLayer = this.createMarkersLayer(this.options.markers);
            map.addLayer(this.markersLayer);
        }

        if (
            this.options.playerMarkers &&
            this.options.playerMarkers.length > 0
        ) {
            this.playerMarkersLayer = this.createMarkersLayer(
                this.options.playerMarkers
            );
            map.addLayer(this.playerMarkersLayer);
        }

        if (this.options.background) {
            if (typeof mapElement === "string") {
                const element = document.getElementById(mapElement);
                if (element)
                    element.style.backgroundColor = this.options.background;
            } else {
                mapElement.style.backgroundColor = this.options.background;
            }
        }

        this.olMap = map;

        this.updateGraticule();
        this.updateScaleBar();
        this.updateMarkersLayer();
        this.updatePlayerMarkersLayer();
        this.olMap.addControl(this.createContextMenu());

        this.redDotMarker = new RedDotMarker(
            this.olMap,
            this.dataProjection!,
            this.viewProjection!
        );

        this.centerOnRedDotMarker();
    }

    center(blockCoordinates: [number, number]): void {
        const view = this.olMap!.getView();
        const v = ol.proj.transform(
            blockCoordinates,
            this.dataProjection!,
            this.viewProjection!
        );
        view.setCenter(v);
    }

    centerOnRedDotMarker(): void {
        const c = this.redDotMarker.getCoordinates();
        if (!c) return;

        this.center(c);
    }

    placeRedDotMarker(coordinates?: [number, number]): void {
        this.redDotMarker.setCoordinates(coordinates);
    }

    createMarkersLayer(markers: MarkerItem[]): VectorLayer<VectorSource> {
        const features: Feature<Point>[] = [];

        for (let i = 0; i < markers.length; i++) {
            const item = markers[i];
            const longitude = item.x;
            const latitude = item.z;

            const feature = new Feature({
                geometry: new Point(
                    ol.proj.transform(
                        [longitude, latitude],
                        this.dataProjection!,
                        this.viewProjection!
                    )
                ),
            });

            const style = new Style();
            if (item.image) {
                style.setImage(
                    new Icon({
                        src: item.image,
                        anchor: item.imageAnchor,
                        scale: item.imageScale,
                    })
                );
            }

            if (item.text) {
                style.setText(
                    new Text({
                        text: item.text,
                        font: item.font,
                        offsetX: item.offsetX,
                        offsetY: item.offsetY,
                        fill: item.textColor
                            ? new Fill({
                                  color: item.textColor,
                              })
                            : undefined,
                        padding: item.textPadding ?? [2, 4, 2, 4],
                        stroke: item.textStrokeColor
                            ? new Stroke({
                                  color: item.textStrokeColor,
                                  width: item.textStrokeWidth,
                              })
                            : undefined,
                        backgroundFill: item.textBackgroundColor
                            ? new Fill({
                                  color: item.textBackgroundColor,
                              })
                            : undefined,
                        backgroundStroke: item.textBackgroundStrokeColor
                            ? new Stroke({
                                  color: item.textBackgroundStrokeColor,
                                  width: item.textBackgroundStrokeWidth,
                              })
                            : undefined,
                    })
                );
            }

            feature.setStyle(style);
            features.push(feature);
        }

        const vectorSource = new VectorSource({
            features: features,
        });

        const vectorLayer = new VectorLayer({
            source: vectorSource,
        });
        return vectorLayer;
    }

    static defaultPlayerMarkerStyle: Partial<MarkerItem> = {
        image: "playerimages/default.png",
        imageAnchor: [0.5, 0.5],
        imageScale: 0.25,
        textColor: "white",
        offsetX: 0,
        offsetY: 20,
        font: "14px Arial",
        textBackgroundColor: "#00000088",
        textPadding: [2, 4, 2, 4],
    };

    static playerToMarker(player: Player): MarkerItem {
        const marker: MarkerItem = {
            ...(Unmined.defaultPlayerMarkerStyle as MarkerItem),
            x: player.x,
            z: player.z,
            text: player.name,
        };
        return marker;
    }

    static createPlayerMarkers(players: Player[]): MarkerItem[] {
        const markers = players.map((player) => Unmined.playerToMarker(player));
        return markers;
    }

    updateGraticule(): void {
        if (!this.olMap) return;

        if (this.gridLayer) this.olMap.removeLayer(this.gridLayer);
        if (this.coordinateLayer) this.olMap.removeLayer(this.coordinateLayer);

        this.gridLayer = null;
        if (!this.options.enableGrid) return;

        this.gridLayer = this.createGraticuleLayer(false);
        this.coordinateLayer = this.createGraticuleLayer(true);

        this.gridLayer?.setVisible(this.options.showGrid!);
        this.coordinateLayer?.setVisible(this.options.showGrid!);

        this.gridLayer.setZIndex(500);
        this.coordinateLayer.setZIndex(10000);

        this.olMap.addLayer(this.gridLayer);
        this.olMap.addLayer(this.coordinateLayer);
    }

    private createGraticuleLayer(coord: boolean): Graticule {
        const intervalCount = this.olMap!.getView().getMaxZoom() + 2;
        const graticuleIntervals = new Array(intervalCount);

        if (this.options.binaryGrid) {
            let base = 16;
            for (let z = 0; z < intervalCount; ++z) {
                const intervalInBlocks = base;
                const intervalInDegrees = ol.proj.transform(
                    [intervalInBlocks, intervalInBlocks],
                    this.dataProjection!,
                    this.viewProjection!
                )[0];
                graticuleIntervals[intervalCount - 1 - z] = intervalInDegrees;
                base *= 2;
            }
        } else {
            const factors = [1, 2, 5];
            let base = 10;
            let factorIndex = 0;
            for (let z = 0; z < intervalCount; ++z) {
                const intervalInBlocks =
                    base * factors[factorIndex++ % factors.length];
                const intervalInDegrees = ol.proj.transform(
                    [intervalInBlocks, intervalInBlocks],
                    this.dataProjection!,
                    this.viewProjection!
                )[0];
                graticuleIntervals[intervalCount - 1 - z] = intervalInDegrees;
                if (factorIndex % factors.length === 0) base *= 10;
            }
        }

        const graticuleLabelStyle = new Text({
            font: "14px sans-serif",
            placement: "point",
            fill: new Fill({ color: "#fff" }),
            stroke: new Stroke({ color: "#000", width: 2 }),
        });

        const graticuleLonLabelStyle = graticuleLabelStyle.clone();
        graticuleLonLabelStyle.setOffsetY(10);

        const graticuleLatLabelStyle = graticuleLabelStyle.clone();
        graticuleLatLabelStyle.setOffsetX(-2);
        graticuleLatLabelStyle.setTextAlign("right");

        const graticuleStrokeStyle = coord
            ? new Stroke({
                  color: "rgba(0, 0, 0, 0)",
                  width: 0,
              })
            : new Stroke({
                  color: "rgb(0,0,0)",
                  width: 0.5,
              });

        const graticuleLayer = new Graticule({
            strokeStyle: graticuleStrokeStyle,
            showLabels: coord,
            wrapX: false,
            targetSize: this.options.denseGrid ? 60 : 120,
            intervals: graticuleIntervals,
            lonLabelFormatter: coord
                ? (lon: number) => {
                      const c = new Point(
                          ol.proj.transform(
                              [lon, 0],
                              this.viewProjection!,
                              this.dataProjection!
                          )
                      ).getFirstCoordinate();
                      const l = Math.round(c[0]);
                      if (l === 0) return "x = 0";
                      return l.toString();
                  }
                : undefined,
            latLabelFormatter: coord
                ? (lat: number) => {
                      const c = new Point(
                          ol.proj.transform(
                              [0, lat],
                              this.viewProjection!,
                              this.dataProjection!
                          )
                      ).getFirstCoordinate();
                      const l = Math.round(c[1]);
                      if (l === 0) return "z = 0";
                      return l.toString();
                  }
                : undefined,
            lonLabelStyle: coord ? graticuleLonLabelStyle : undefined,
            latLabelStyle: coord ? graticuleLatLabelStyle : undefined,
            lonLabelPosition: 1,
            latLabelPosition: 1,
        });
        return graticuleLayer;
    }

    static copyToClipboard(text: string, toast?: string): void {
        if (
            !navigator ||
            !navigator.clipboard ||
            !navigator.clipboard.writeText
        ) {
            Unmined.toast("Clipboard is not accessible");
            return;
        }

        navigator.clipboard.writeText(text);
        Unmined.toast(toast ?? "Copied!");
    }

    static toast(message: string): void {
        Toastify({
            text: message,
            duration: 2000,
            gravity: "top",
            position: "center",
        }).showToast();
    }

    createContextMenu(): any {
        const contextmenu = new ContextMenu({
            width: 220,
            defaultItems: false,
            items: [],
        });

        contextmenu.on("open", (evt: any) => {
            const coordinates = ol.proj.transform(
                this.olMap!.getEventCoordinate(evt.originalEvent),
                this.viewProjection!,
                this.dataProjection!
            );

            coordinates[0] = Math.round(coordinates[0]);
            coordinates[1] = Math.round(coordinates[1]);

            contextmenu.clear();
            contextmenu.push({
                text: `/tp ${coordinates[0]} ~ ${coordinates[1]}`,
                callback: () => {
                    Unmined.copyToClipboard(
                        `/tp ${coordinates[0]} ~ ${coordinates[1]}`
                    );
                },
            });
            contextmenu.push("-");

            contextmenu.push({
                text: `Place red dot marker here`,
                classname: "menuitem-reddot",
                callback: () => {
                    this.placeRedDotMarker([coordinates[0], coordinates[1]]);
                },
            });

            if (this.redDotMarker.getCoordinates()) {
                contextmenu.push({
                    text: `Copy marker link`,
                    callback: () => {
                        Unmined.copyToClipboard(window.location.href);
                    },
                });
                contextmenu.push({
                    text: `Clear marker`,
                    callback: () => {
                        this.placeRedDotMarker(undefined);
                    },
                });
            }
            contextmenu.push("-");

            if (this.playerMarkersLayer) {
                contextmenu.push({
                    classname: this.options.showPlayers
                        ? "menuitem-checked"
                        : "menuitem-unchecked",
                    text: "Show players",
                    callback: () => this.togglePlayers(),
                });
            }

            if (this.markersLayer) {
                contextmenu.push({
                    classname: this.options.showMarkers
                        ? "menuitem-checked"
                        : "menuitem-unchecked",
                    text: "Show markers",
                    callback: () => this.toggleMarkers(),
                });
            }

            if (this.markersLayer || this.playerMarkersLayer) {
                contextmenu.push("-");
            }

            if (this.options.enableGrid) {
                contextmenu.push({
                    classname: this.options.showGrid
                        ? "menuitem-checked"
                        : "menuitem-unchecked",
                    text: "Show grid",
                    callback: () => this.toggleGrid(),
                });
                contextmenu.push({
                    classname: this.options.denseGrid
                        ? "menuitem-checked"
                        : "menuitem-unchecked",
                    text: "Dense grid",
                    callback: () => this.toggleGridInterval(),
                });
                contextmenu.push({
                    classname: this.options.binaryGrid
                        ? "menuitem-checked"
                        : "menuitem-unchecked",
                    text: "Binary coordinates",
                    callback: () => this.toggleBinaryGrid(),
                });
            }

            contextmenu.push({
                classname: this.options.showScaleBar
                    ? "menuitem-checked"
                    : "menuitem-unchecked",
                text: "Show scalebar",
                callback: () => this.toggleScaleBar(),
            });
        });

        return contextmenu;
    }

    toggleGridInterval(): void {
        this.options.denseGrid = !this.options.denseGrid;
        this.updateGraticule();
        this.saveSettings();
    }

    toggleBinaryGrid(): void {
        this.options.binaryGrid = !this.options.binaryGrid;
        this.updateGraticule();
        this.saveSettings();
    }

    toggleGrid(): void {
        this.options.showGrid = !this.options.showGrid;
        this.updateGraticule();
        this.saveSettings();
    }

    toggleScaleBar(): void {
        this.options.showScaleBar = !this.options.showScaleBar;
        this.updateScaleBar();
        this.saveSettings();
    }

    toggleMarkers(): void {
        this.options.showMarkers = !this.options.showMarkers;
        this.updateMarkersLayer();
        this.saveSettings();
    }

    togglePlayers(): void {
        this.options.showPlayers = !this.options.showPlayers;
        this.updatePlayerMarkersLayer();
        this.saveSettings();
    }

    loadSettings(): void {
        const mapSettings = (() => {
            try {
                const s = localStorage.getItem("mapSettings");
                if (!s) return undefined;
                return JSON.parse(s) as MapSettings;
            } catch {
                return undefined;
            }
        })();

        if (!mapSettings) return;

        this.options.showScaleBar =
            mapSettings.showScaleBar ?? this.options.showScaleBar;
        this.options.showGrid = mapSettings.showGrid ?? this.options.showGrid;
        this.options.binaryGrid =
            mapSettings.binaryGrid ?? this.options.binaryGrid;
        this.options.denseGrid =
            mapSettings.denseGrid ?? this.options.denseGrid;
        this.options.showMarkers =
            mapSettings.showMarkers ?? this.options.showMarkers;
        this.options.showPlayers =
            mapSettings.showPlayers ?? this.options.showPlayers;
    }

    saveSettings(): void {
        const mapSettings: MapSettings = {
            showScaleBar: this.options.showScaleBar!,
            showGrid: this.options.showGrid!,
            binaryGrid: this.options.binaryGrid!,
            denseGrid: this.options.denseGrid!,
            showMarkers: this.options.showMarkers!,
            showPlayers: this.options.showPlayers!,
        };
        localStorage.setItem("mapSettings", JSON.stringify(mapSettings));
    }

    updateMarkersLayer(): void {
        this.markersLayer?.setVisible(this.options.showMarkers!);
    }

    updatePlayerMarkersLayer(): void {
        this.playerMarkersLayer?.setVisible(this.options.showPlayers!);
    }

    updateScaleBar(): void {
        if (!this.options.showScaleBar && this.scaleLine) {
            this.olMap!.removeControl(this.scaleLine);
            this.scaleLine = null;
        } else if (this.options.showScaleBar && !this.scaleLine) {
            this.scaleLine = new ScaleLine({
                bar: true,
                minWidth: 200,
            });
            this.olMap!.addControl(this.scaleLine);
        }
    }

    private initProjections(maxCoordValue: number): void {
        const blocksPerDegrees = Math.max(30000000, maxCoordValue) / 270;
        const radius = 270;

        this.viewProjection = new Projection({
            code: "VIEW",
            units: "degrees",
            extent: [-radius, -radius, +radius, +radius],
            worldExtent: [-radius, -radius, +radius, +radius],
            global: true,
        });

        this.dataProjection = new Projection({
            code: "DATA",
            units: "pixels",
            metersPerUnit: 1,
        });

        // Coordinate transformation between view and data
        // OpenLayers Y is positive up, world Y is positive down
        ol.proj.addCoordinateTransforms(
            this.viewProjection,
            this.dataProjection,
            function (coordinate: number[]): number[] {
                return [
                    coordinate[0] * blocksPerDegrees,
                    -coordinate[1] * blocksPerDegrees,
                ];
            },
            function (coordinate: number[]): number[] {
                return [
                    coordinate[0] / blocksPerDegrees,
                    -coordinate[1] / blocksPerDegrees,
                ];
            }
        );
    }
}

export { Unmined, RegionMap, RedDotMarker };
