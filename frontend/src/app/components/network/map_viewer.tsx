import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router";
import OlMap from "ol/Map";
import View from "ol/View";
import Feature from "ol/Feature";
import TileLayer from "ol/layer/Tile";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import XYZ from "ol/source/XYZ";
import MousePosition from "ol/control/MousePosition";
import { Point, Polygon } from "ol/geom";
import {
    Circle as CircleStyle,
    Fill,
    Icon,
    Stroke,
    Style,
    Text,
} from "ol/style";
import type { FeatureLike } from "ol/Feature";

import { MARKER_KINDS } from "../../types/map";
import type { MarkerKind } from "../../types/map";
import { DIMENSIONS } from "../../types/trains";
import { factionColor, withAlpha } from "../../utils/mapcolors";
import { iconUrl } from "../../utils/mapicons";
import { buildGeometry } from "../../utils/unmined";
import type { MapGeometry, UnminedData } from "../../utils/unmined";
import { useMapOverlay, useUnminedData } from "../../hooks/network/map";
import MapEditor, { type EntityRef } from "./map_editor";

export interface Selection {
    entity: EntityRef | null;
    stationId: number | null;
    /** The icon shown in the card, if the element has one. */
    iconKind: MarkerKind | null;
    title: string;
    kind: string;
    lines: string[];
}

const LEGEND_KEY = "aide.map.legendOpen";

/** The legend starts as the viewer left it; folded on a small screen. */
function initialLegendOpen(): boolean {
    try {
        const saved = localStorage.getItem(LEGEND_KEY);
        if (saved !== null) return saved === "1";
    } catch {
        // No storage (private window...): the default below
    }
    return !window.matchMedia("(max-width: 800px)").matches;
}

type LayerKey = "territories" | "stations" | "markers" | "players";

const LAYER_LABELS: Record<LayerKey, string> = {
    territories: "Territoires",
    stations: "Gares",
    markers: "Points d'intérêt",
    players: "Joueurs en ligne",
};

const Z_INDEX: Record<LayerKey, number> = {
    territories: 10,
    stations: 30,
    markers: 40,
    players: 50,
};

function labelStyle(text: string, color = "#fff") {
    return new Text({
        text,
        offsetY: -14,
        font: "600 12px sans-serif",
        fill: new Fill({ color }),
        stroke: new Stroke({ color: "rgba(0,0,0,0.85)", width: 3 }),
    });
}

const ICON_SIZE = { station: 32, other: 40 };
const iconCache = new Map<string, Icon>();

const dotCache = new Map<string, CircleStyle>();

function pointDot(color: string): CircleStyle {
    let circle = dotCache.get(color);
    if (!circle) {
        circle = new CircleStyle({
            radius: 10,
            fill: new Fill({ color }),
            stroke: new Stroke({ color: "#1b1b1b", width: 3 }),
        });
        dotCache.set(color, circle);
    }
    return circle;
}

/* The icon of a kind and colour (built once: the image is loaded once), with
   a label. An explored structure is faded: nothing left to take there. */
function iconStyle(
    kind: MarkerKind,
    text: string,
    color?: string,
    explored = false,
) {
    if (kind === "generic" && color) {
        // A generic point with a chosen colour: a dot like generic.svg
        return new Style({
            image: pointDot(color),
            text: new Text({
                text,
                offsetY: 22,
                font: "600 12px sans-serif",
                fill: new Fill({ color: "#fff" }),
                stroke: new Stroke({ color: "rgba(0,0,0,0.85)", width: 3 }),
            }),
        });
    }
    const key = `${kind}:${color ?? ""}:${explored ? "x" : ""}`;
    let icon = iconCache.get(key);
    if (!icon) {
        const size = kind === "station" ? ICON_SIZE.station : ICON_SIZE.other;
        icon = new Icon({
            src: iconUrl(kind),
            width: size,
            height: size,
            color,
            opacity: explored ? 0.45 : 1,
        });
        iconCache.set(key, icon);
    }
    return new Style({
        image: icon,
        text: new Text({
            text,
            offsetY: kind === "station" ? 26 : 30,
            font: "600 12px sans-serif",
            fill: new Fill({ color: "#fff" }),
            stroke: new Stroke({ color: "rgba(0,0,0,0.85)", width: 3 }),
        }),
    });
}

function dot(color: string, radius: number, text?: string) {
    return new Style({
        image: new CircleStyle({
            radius,
            fill: new Fill({ color }),
            stroke: new Stroke({ color: "#000", width: 1.5 }),
        }),
        text: text ? labelStyle(text) : undefined,
    });
}

function MapCanvas({
    folder,
    unmined,
}: {
    folder: string;
    unmined: UnminedData;
}) {
    const overlay = useMapOverlay(folder);
    const container = useRef<HTMLDivElement>(null);
    const mapRef = useRef<OlMap | null>(null);
    const geometryRef = useRef<MapGeometry | null>(null);
    const layers = useRef<Record<LayerKey, VectorLayer<VectorSource>> | null>(
        null,
    );
    const hiddenFactions = useRef<Set<number>>(new Set());
    const hiddenKinds = useRef<Set<MarkerKind>>(new Set());
    // Set by the editor: a drawing in progress ignores clicks, and a pick
    // takes the next click as coordinates.
    const busyRef = useRef(false);
    const pickRef = useRef<((block: [number, number]) => void) | null>(null);
    const [mapState, setMapState] = useState<{
        map: OlMap;
        geometry: MapGeometry;
        layers: Record<LayerKey, VectorLayer<VectorSource>>;
    } | null>(null);

    const [visible, setVisible] = useState<Record<LayerKey, boolean>>({
        territories: true,
        stations: true,
        markers: true,
        players: true,
    });
    const [hidden, setHidden] = useState<number[]>([]);
    const [hiddenKindList, setHiddenKindList] = useState<MarkerKind[]>([]);
    const [selection, setSelection] = useState<Selection | null>(null);
    const [coords, setCoords] = useState({ x: "", z: "" });
    const [goError, setGoError] = useState<string | null>(null);
    const [gotoOpen, setGotoOpen] = useState(false);
    const [legendOpen, setLegendOpen] = useState(initialLegendOpen);

    function toggleLegend() {
        setLegendOpen((open) => {
            try {
                localStorage.setItem(LEGEND_KEY, open ? "0" : "1");
            } catch {
                // Not remembered, still toggled
            }
            return !open;
        });
    }

    // The map itself: tiles and empty layers, created once per export.
    useEffect(() => {
        if (!container.current) return;
        const geometry = buildGeometry(
            folder,
            unmined.properties,
            unmined.regions,
        );
        geometryRef.current = geometry;
        const props = unmined.properties;

        const tiles = new TileLayer({
            source: new XYZ({
                projection: geometry.projection,
                tileGrid: geometry.tileGrid,
                tilePixelRatio: geometry.pixelRatio,
                tileSize: 256 / geometry.pixelRatio,
                tileUrlFunction: (coordinate) =>
                    geometry.tileUrl(
                        coordinate[0],
                        coordinate[1],
                        coordinate[2],
                    ),
            }),
        });

        const make = (key: LayerKey) =>
            new VectorLayer({
                source: new VectorSource(),
                zIndex: Z_INDEX[key],
            });
        const vectors: Record<LayerKey, VectorLayer<VectorSource>> = {
            territories: make("territories"),
            stations: make("stations"),
            markers: make("markers"),
            players: make("players"),
        };
        layers.current = vectors;

        vectors.territories.setStyle((feature: FeatureLike) => {
            const factionId = feature.get("factionId") as number;
            if (hiddenFactions.current.has(factionId)) return undefined;
            const color = feature.get("color") as string;
            return new Style({
                fill: new Fill({ color: withAlpha(color, 0.22) }),
                stroke: new Stroke({ color, width: 2.5 }),
                text: new Text({
                    text: feature.get("title") as string,
                    font: "600 13px sans-serif",
                    fill: new Fill({ color: "#fff" }),
                    stroke: new Stroke({ color: "rgba(0,0,0,0.85)", width: 3 }),
                    overflow: true,
                }),
            });
        });
        // Stations and points of interest share the kinds' icons and can be hidden kind by kind from the legend.
        const kindStyle = (feature: FeatureLike) => {
            const kind = feature.get("markerKind") as MarkerKind;
            if (hiddenKinds.current.has(kind)) return undefined;
            return iconStyle(
                kind,
                feature.get("title") as string,
                feature.get("color") as string | undefined,
                feature.get("explored") === true,
            );
        };
        vectors.stations.setStyle(kindStyle);
        vectors.markers.setStyle(kindStyle);
        // The icons are pixel art (often 16x16 textures): scale them without smoothing so that they stay crisp.
        for (const layer of [vectors.stations, vectors.markers]) {
            layer.on("prerender", (event) => {
                const context = event.context as CanvasRenderingContext2D;
                context.imageSmoothingEnabled = false;
            });
        }
        vectors.players.setStyle((feature: FeatureLike) =>
            dot("#e53935", 5, feature.get("title") as string),
        );

        const center = geometry.toView([props.centerX, props.centerZ]);
        const map = new OlMap({
            target: container.current,
            layers: [tiles, ...Object.values(vectors)],
            controls: [],
            view: new View({
                projection: geometry.projection,
                center,
                extent: geometry.extent,
                resolutions: geometry.resolutions,
                maxZoom: geometry.zoomLevels,
                zoom: Math.min(
                    Math.max(geometry.defaultZoom, 0),
                    geometry.zoomLevels,
                ),
                constrainResolution: true,
                showFullExtent: true,
                constrainOnlyCenter: true,
                enableRotation: false,
            }),
        });
        map.addControl(
            new MousePosition({
                className: "map-mouse-position",
                coordinateFormat: (c) => {
                    if (!c) return "";
                    const [x, z] = geometry.toBlocks(c);
                    return `X ${Math.round(x)}   Z ${Math.round(z)}`;
                },
            }),
        );

        map.on("singleclick", (event) => {
            // While a point is being placed, every click moves it
            if (pickRef.current) {
                pickRef.current(geometry.toBlocks(event.coordinate));
                return;
            }
            if (busyRef.current) return;
            const feature = map.forEachFeatureAtPixel(event.pixel, (f) => f, {
                hitTolerance: 6,
            });
            if (!feature) {
                setSelection(null);
                return;
            }
            const entity = feature.get("entity") as
                EntityRef["type"] | undefined;
            setSelection({
                entity: entity
                    ? { type: entity, id: feature.get("entityId") as number }
                    : null,
                stationId: (feature.get("stationId") as number) ?? null,
                iconKind: (feature.get("markerKind") as MarkerKind) ?? null,
                title: feature.get("title") as string,
                kind: feature.get("kindLabel") as string,
                lines: (feature.get("details") as string[]) ?? [],
            });
        });

        mapRef.current = map;
        setMapState({ map, geometry, layers: vectors });
        return () => {
            setMapState(null);
            map.setTarget(undefined);
            map.dispose();
            mapRef.current = null;
            layers.current = null;
        };
    }, [folder, unmined]);

    // Territories
    useEffect(() => {
        const geometry = geometryRef.current;
        const source = layers.current?.territories.getSource();
        if (!geometry || !source) return;
        source.clear();
        source.addFeatures(
            overlay.territories.map((t) => {
                const ring = t.points.map((p) => geometry.toView(p));
                ring.push(ring[0]);
                const faction = t.faction_name ?? `Faction ${t.faction_id}`;
                return new Feature({
                    geometry: new Polygon([ring]),
                    title: t.name,
                    kindLabel: "Territoire",
                    entity: "territory",
                    entityId: t.territory_id,
                    factionId: t.faction_id,
                    color: factionColor(t.faction_id, t.color),
                    details: [
                        `Faction : ${faction}`,
                        ...(t.description ? [t.description] : []),
                    ],
                });
            }),
        );
    }, [overlay.territories, unmined, folder]);

    // Stations (the lines are drawn on the network page, not here)
    useEffect(() => {
        const geometry = geometryRef.current;
        const stationSource = layers.current?.stations.getSource();
        if (!geometry || !stationSource) return;
        stationSource.clear();
        stationSource.addFeatures(
            overlay.stations.map((s) => {
                const served = overlay.lines
                    .filter((l) =>
                        l.stops.some(
                            (st) => st.station.station_id === s.station_id,
                        ),
                    )
                    .map((l) => l.code);
                return new Feature({
                    geometry: new Point(geometry.toView([s.x, s.z])),
                    title: s.name,
                    kindLabel: MARKER_KINDS.station,
                    markerKind: "station",
                    stationId: s.station_id,
                    details: [
                        `X ${s.x}   Z ${s.z}`,
                        ...(served.length
                            ? [`Lignes : ${served.join(", ")}`]
                            : []),
                        ...(s.description ? [s.description] : []),
                    ],
                });
            }),
        );
    }, [overlay.lines, overlay.stations, unmined, folder]);

    // Points of interest
    useEffect(() => {
        const geometry = geometryRef.current;
        const source = layers.current?.markers.getSource();
        if (!geometry || !source) return;
        source.clear();
        const colors = new Map<number, string | null>(
            overlay.territories.map((t) => [t.faction_id, t.color]),
        );
        source.addFeatures(
            overlay.markers.map(
                (m) =>
                    new Feature({
                        geometry: new Point(geometry.toView([m.x, m.z])),
                        title: m.label,
                        entity: "marker",
                        entityId: m.marker_id,
                        color:
                            m.kind === "city" && m.faction_id != null
                                ? factionColor(
                                      m.faction_id,
                                      colors.get(m.faction_id),
                                  )
                                : m.kind === "generic"
                                  ? (m.color ?? undefined)
                                  : undefined,
                        markerKind: m.kind,
                        explored: m.explored,
                        kindLabel: MARKER_KINDS[m.kind] ?? "Point d'intérêt",
                        details: [
                            `X ${m.x}   Z ${m.z}`,
                            ...(m.owner_name && m.kind !== "spawn"
                                ? [`Par : ${m.owner_name}`]
                                : []),
                            ...(m.description ? [m.description] : []),
                        ],
                    }),
            ),
        );
    }, [overlay.markers, overlay.territories, unmined, folder]);

    // Online players, as written by the last export
    useEffect(() => {
        const geometry = geometryRef.current;
        const source = layers.current?.players.getSource();
        if (!geometry || !source) return;
        source.clear();
        source.addFeatures(
            unmined.players.map(
                (p) =>
                    new Feature({
                        geometry: new Point(geometry.toView([p.x, p.z])),
                        title: p.name,
                        kindLabel: "Joueur",
                        details: [
                            `X ${Math.round(p.x)}   Z ${Math.round(p.z)}`,
                        ],
                    }),
            ),
        );
    }, [unmined, folder]);

    useEffect(() => {
        if (!layers.current) return;
        for (const key of Object.keys(visible) as LayerKey[]) {
            layers.current[key].setVisible(visible[key]);
        }
    }, [visible, unmined, folder]);

    useEffect(() => {
        hiddenFactions.current = new Set(hidden);
        layers.current?.territories.changed();
    }, [hidden]);

    useEffect(() => {
        hiddenKinds.current = new Set(hiddenKindList);
        layers.current?.stations.changed();
        layers.current?.markers.changed();
    }, [hiddenKindList]);

    // The kinds of the points on the map, in the order of the list of kinds.
    // Stations are not among them: their own layer ("Gares") shows or hides
    // them.
    const kinds = useMemo(() => {
        const present = new Set<MarkerKind>(overlay.markers.map((m) => m.kind));
        return (Object.keys(MARKER_KINDS) as MarkerKind[]).filter((k) =>
            present.has(k),
        );
    }, [overlay.markers]);

    const factions = useMemo(() => {
        const seen = new Map<number, { name: string; color: string }>();
        for (const t of overlay.territories) {
            if (!seen.has(t.faction_id)) {
                seen.set(t.faction_id, {
                    name: t.faction_name ?? `Faction ${t.faction_id}`,
                    color: factionColor(t.faction_id, t.color),
                });
            }
        }
        return [...seen.entries()].sort((a, b) =>
            a[1].name.localeCompare(b[1].name),
        );
    }, [overlay.territories]);

    function goTo(event: FormEvent) {
        event.preventDefault();
        const geometry = geometryRef.current;
        const map = mapRef.current;
        const x = Number(coords.x);
        const z = Number(coords.z);
        if (
            !geometry ||
            !map ||
            coords.x.trim() === "" ||
            coords.z.trim() === "" ||
            !Number.isFinite(x) ||
            !Number.isFinite(z)
        ) {
            setGoError("Entrez deux nombres.");
            return;
        }
        setGoError(null);
        setGotoOpen(false);
        map.getView().animate({
            center: geometry.toView([x, z]),
            duration: 400,
        });
    }

    function toggleKind(kind: MarkerKind) {
        setHiddenKindList((current) =>
            current.includes(kind)
                ? current.filter((k) => k !== kind)
                : [...current, kind],
        );
    }

    function toggleFaction(id: number) {
        setHidden((current) =>
            current.includes(id)
                ? current.filter((f) => f !== id)
                : [...current, id],
        );
    }

    // Going to coordinates is rare: a small button, opened into a form
    const gotoControl = gotoOpen ? (
        <form
            className="map-goto"
            onSubmit={goTo}
            onKeyDown={(e) => {
                if (e.key === "Escape") setGotoOpen(false);
            }}
        >
            <input
                type="text"
                inputMode="numeric"
                placeholder="X"
                aria-label="Aller à X"
                autoFocus
                value={coords.x}
                onChange={(e) => setCoords({ ...coords, x: e.target.value })}
            />
            <input
                type="text"
                inputMode="numeric"
                placeholder="Z"
                aria-label="Aller à Z"
                value={coords.z}
                onChange={(e) => setCoords({ ...coords, z: e.target.value })}
            />
            <button type="submit" className="map-icon-button" title="Aller">
                →
            </button>
            <button
                type="button"
                className="map-close"
                aria-label="Fermer"
                onClick={() => {
                    setGotoOpen(false);
                    setGoError(null);
                }}
            >
                ×
            </button>
            {goError && <p className="map-error">{goError}</p>}
        </form>
    ) : (
        <button
            type="button"
            className="map-icon-button"
            title="Aller aux coordonnées"
            aria-label="Aller aux coordonnées"
            onClick={() => setGotoOpen(true)}
        >
            ⌖
        </button>
    );

    return (
        <div className="map-viewer">
            <div
                ref={container}
                className="map-canvas"
                style={{ background: unmined.properties.background || "#000" }}
                aria-label="Carte du serveur"
            />

            {/* Left: where to go, what to add, what is selected */}
            <div className="map-left">
                {mapState && (
                    <MapEditor
                        folder={folder}
                        map={mapState.map}
                        geometry={mapState.geometry}
                        territories={overlay.territories}
                        markers={overlay.markers}
                        selection={selection}
                        onCloseSelection={() => setSelection(null)}
                        busyRef={busyRef}
                        pickRef={pickRef}
                        onRefresh={overlay.refresh}
                        onChanged={() => {
                            setSelection(null);
                            overlay.refresh();
                        }}
                        leading={gotoControl}
                    />
                )}
            </div>

            {/* Right: what is shown, folded into a button when not needed */}
            <aside
                className={`map-float map-legend${legendOpen ? " open" : ""}`}
                aria-label="Légende de la carte"
            >
                <button
                    type="button"
                    className="map-legend-toggle"
                    aria-expanded={legendOpen}
                    onClick={toggleLegend}
                >
                    <span aria-hidden="true">☰</span> Légende
                </button>

                {legendOpen && (
                    <div className="map-legend-body">
                        <details open>
                            <summary>Calques</summary>
                            <ul className="map-layers">
                                {(Object.keys(LAYER_LABELS) as LayerKey[]).map(
                                    (key) => (
                                        <li key={key}>
                                            <label>
                                                <input
                                                    type="checkbox"
                                                    checked={visible[key]}
                                                    onChange={() =>
                                                        setVisible((v) => ({
                                                            ...v,
                                                            [key]: !v[key],
                                                        }))
                                                    }
                                                />
                                                {LAYER_LABELS[key]}
                                            </label>
                                        </li>
                                    ),
                                )}
                            </ul>
                        </details>

                        {kinds.length > 0 && (
                            <details open>
                                <summary>Types de points</summary>
                                <div className="map-kind-chips">
                                    {kinds.map((kind) => {
                                        const shown =
                                            !hiddenKindList.includes(kind);
                                        return (
                                            <button
                                                key={kind}
                                                type="button"
                                                className="map-chip"
                                                aria-pressed={shown}
                                                title={
                                                    shown
                                                        ? "Cliquer pour masquer"
                                                        : "Cliquer pour afficher"
                                                }
                                                onClick={() => toggleKind(kind)}
                                            >
                                                <img
                                                    className="map-kind-icon"
                                                    src={iconUrl(kind)}
                                                    alt=""
                                                />
                                                {MARKER_KINDS[kind]}
                                            </button>
                                        );
                                    })}
                                </div>
                            </details>
                        )}

                        {factions.length > 0 && (
                            <details>
                                <summary>Factions ({factions.length})</summary>
                                <ul className="map-layers">
                                    {factions.map(([id, f]) => (
                                        <li key={id}>
                                            <label>
                                                <input
                                                    type="checkbox"
                                                    checked={
                                                        !hidden.includes(id)
                                                    }
                                                    onChange={() =>
                                                        toggleFaction(id)
                                                    }
                                                />
                                                <span
                                                    className="map-swatch"
                                                    style={{
                                                        background: f.color,
                                                    }}
                                                />
                                                {f.name}
                                            </label>
                                        </li>
                                    ))}
                                </ul>
                            </details>
                        )}

                        <p className="map-hint">
                            {DIMENSIONS[overlay.dimension]} ·{" "}
                            <Link to="/network">Lignes de train</Link>
                        </p>
                    </div>
                )}
            </aside>

            {overlay.errors.length > 0 && (
                <p className="map-float map-errors map-error" role="alert">
                    {overlay.errors.join(" - ")}
                </p>
            )}
        </div>
    );
}

export default function MapViewer({ folder }: { folder: string }) {
    const { unmined, error, loading } = useUnminedData(folder);

    if (loading) return <p className="map-status">Chargement de la carte...</p>;
    if (error || !unmined) {
        return (
            <p className="map-status map-error">
                {error ?? "Carte indisponible."}
            </p>
        );
    }
    return <MapCanvas folder={folder} unmined={unmined} />;
}
