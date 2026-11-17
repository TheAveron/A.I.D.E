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

interface Selection {
    entity: EntityRef | null;
    title: string;
    kind: string;
    lines: string[];
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

/** The icon of a kind (built once: the image is loaded once), with a label. */
function iconStyle(kind: MarkerKind, text: string) {
    let icon = iconCache.get(kind);
    if (!icon) {
        const size = kind === "station" ? ICON_SIZE.station : ICON_SIZE.other;
        icon = new Icon({ src: iconUrl(kind), width: size, height: size });
        iconCache.set(kind, icon);
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
        // Stations and points of interest share the kinds' icons and can be
        // hidden kind by kind from the legend.
        const kindStyle = (feature: FeatureLike) => {
            const kind = feature.get("markerKind") as MarkerKind;
            if (hiddenKinds.current.has(kind)) return undefined;
            return iconStyle(kind, feature.get("title") as string);
        };
        vectors.stations.setStyle(kindStyle);
        vectors.markers.setStyle(kindStyle);
        // The icons are pixel art (often 16x16 textures): scale them without
        // smoothing so that they stay crisp.
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
            if (pickRef.current) {
                const pick = pickRef.current;
                pickRef.current = null;
                pick(geometry.toBlocks(event.coordinate));
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
        source.addFeatures(
            overlay.markers.map(
                (m) =>
                    new Feature({
                        geometry: new Point(geometry.toView([m.x, m.z])),
                        title: m.label,
                        entity: "marker",
                        entityId: m.marker_id,
                        markerKind: m.kind,
                        kindLabel: MARKER_KINDS[m.kind] ?? "Point d'intérêt",
                        details: [
                            `X ${m.x}   Z ${m.z}`,
                            ...(m.owner_name ? [`Par : ${m.owner_name}`] : []),
                            ...(m.description ? [m.description] : []),
                        ],
                    }),
            ),
        );
    }, [overlay.markers, unmined, folder]);

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

    // The kinds on the map, in the order of the list of kinds
    const kinds = useMemo(() => {
        const present = new Set<MarkerKind>(overlay.markers.map((m) => m.kind));
        if (overlay.stations.length > 0) present.add("station");
        return (Object.keys(MARKER_KINDS) as MarkerKind[]).filter((k) =>
            present.has(k),
        );
    }, [overlay.markers, overlay.stations]);

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

    return (
        <div className="map-viewer">
            <div
                ref={container}
                className="map-canvas"
                style={{ background: unmined.properties.background || "#000" }}
                aria-label="Carte du serveur"
            />

            <aside className="map-panel">
                <h3>Calques</h3>
                <ul className="map-layers">
                    {(Object.keys(LAYER_LABELS) as LayerKey[]).map((key) => (
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
                    ))}
                </ul>

                {factions.length > 0 && (
                    <>
                        <h3>Factions</h3>
                        <ul className="map-layers">
                            {factions.map(([id, f]) => (
                                <li key={id}>
                                    <label>
                                        <input
                                            type="checkbox"
                                            checked={!hidden.includes(id)}
                                            onChange={() => toggleFaction(id)}
                                        />
                                        <span
                                            className="map-swatch"
                                            style={{ background: f.color }}
                                        />
                                        {f.name}
                                    </label>
                                </li>
                            ))}
                        </ul>
                    </>
                )}

                {kinds.length > 0 && (
                    <>
                        <h3>Légende</h3>
                        <ul className="map-layers">
                            {kinds.map((kind) => (
                                <li key={kind}>
                                    <label>
                                        <input
                                            type="checkbox"
                                            checked={
                                                !hiddenKindList.includes(kind)
                                            }
                                            onChange={() => toggleKind(kind)}
                                        />
                                        <img
                                            className="map-kind-icon"
                                            src={iconUrl(kind)}
                                            alt=""
                                        />
                                        {MARKER_KINDS[kind]}
                                    </label>
                                </li>
                            ))}
                        </ul>
                    </>
                )}

                <h3>Aller aux coordonnées</h3>
                <form className="map-goto" onSubmit={goTo}>
                    <input
                        type="text"
                        inputMode="numeric"
                        placeholder="X"
                        aria-label="X"
                        value={coords.x}
                        onChange={(e) =>
                            setCoords({ ...coords, x: e.target.value })
                        }
                    />
                    <input
                        type="text"
                        inputMode="numeric"
                        placeholder="Z"
                        aria-label="Z"
                        value={coords.z}
                        onChange={(e) =>
                            setCoords({ ...coords, z: e.target.value })
                        }
                    />
                    <button type="submit">Aller</button>
                </form>
                {goError && <p className="map-error">{goError}</p>}

                {overlay.errors.length > 0 && (
                    <p className="map-error">{overlay.errors.join(" - ")}</p>
                )}
                <p className="map-hint">
                    <Link to="/network">Voir les lignes de train</Link>
                    <br />
                    {DIMENSIONS[overlay.dimension]} - cliquez sur un élément
                    pour le détail.
                </p>

                {mapState && (
                    <MapEditor
                        folder={folder}
                        map={mapState.map}
                        geometry={mapState.geometry}
                        territories={overlay.territories}
                        markers={overlay.markers}
                        selected={selection?.entity ?? null}
                        busyRef={busyRef}
                        pickRef={pickRef}
                        onChanged={() => {
                            setSelection(null);
                            overlay.refresh();
                        }}
                    />
                )}

                {selection && (
                    <div className="map-selection" aria-live="polite">
                        <h3>{selection.title}</h3>
                        <p className="map-selection-kind">{selection.kind}</p>
                        {selection.lines.map((line, i) => (
                            <p key={i}>{line}</p>
                        ))}
                    </div>
                )}
            </aside>
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
