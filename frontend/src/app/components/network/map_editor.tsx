import axios from "axios";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router";
import type { MutableRefObject, ReactNode } from "react";
import type OlMap from "ol/Map";
import Feature from "ol/Feature";
import Draw from "ol/interaction/Draw";
import Modify from "ol/interaction/Modify";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import { Point, Polygon } from "ol/geom";
import { Circle as CircleStyle, Fill, Stroke, Style } from "ol/style";

import { MARKER_KINDS, dimensionOfFolder, isStructure } from "../../types/map";
import type { MarkerKind, MarkerType, TerritoryType } from "../../types/map";
import { getErrorMessage } from "../../utils/apierror";
import {
    DEFAULT_POINT_COLOR,
    PALETTE,
    factionColor,
    normalizeHex,
} from "../../utils/mapcolors";
import { iconUrl } from "../../utils/mapicons";
import type { MapGeometry } from "../../utils/unmined";
import { useFactions } from "../../hooks/factions/factions";
import { useMapRights } from "../../hooks/network/maprights";
import type { Selection } from "./map_viewer";

export interface EntityRef {
    type: "territory" | "marker";
    id: number;
}

type Points = [number, number][];

interface TerritoryDraft {
    kind: "territory";
    id: number | null;
    name: string;
    description: string;
    color: string;
    factionId: number | null;
}

interface MarkerDraft {
    kind: "marker";
    id: number | null;
    label: string;
    description: string;
    markerKind: MarkerKind;
    x: string;
    z: string;
    // A generic point's colour as typed; "" for the default one
    color: string;
    // null: the player's own point; otherwise a faction's
    factionId: number | null;
}

type Draft = TerritoryDraft | MarkerDraft;

/** A colour picker, its hex code (typed or pasted) and a few ready ones. */
function ColorField({
    value,
    onChange,
}: {
    value: string;
    onChange: (value: string) => void;
}) {
    const valid = normalizeHex(value);
    return (
        <div className="map-field">
            <span>Couleur</span>
            <div className="map-color-inputs">
                <input
                    type="color"
                    aria-label="Choisir la couleur"
                    value={valid ?? DEFAULT_POINT_COLOR}
                    onChange={(e) => onChange(e.target.value)}
                />
                <input
                    type="text"
                    className="map-hex"
                    aria-label="Code hexadécimal"
                    placeholder={DEFAULT_POINT_COLOR}
                    maxLength={7}
                    spellCheck={false}
                    aria-invalid={value !== "" && valid === null}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                />
                {value !== "" && (
                    <button
                        type="button"
                        className="map-close"
                        title="Couleur par défaut"
                        aria-label="Couleur par défaut"
                        onClick={() => onChange("")}
                    >
                        ×
                    </button>
                )}
            </div>
            <div className="map-swatches">
                {PALETTE.map((color) => (
                    <button
                        key={color}
                        type="button"
                        className="map-swatch-button"
                        style={{ background: color }}
                        aria-label={color}
                        aria-pressed={valid === color}
                        onClick={() => onChange(color)}
                    />
                ))}
            </div>
        </div>
    );
}

const PREVIEW_STROKE = new Stroke({
    color: "#ffeb3b",
    width: 3,
    lineDash: [8, 6],
});
const PREVIEW_STYLE = new Style({
    stroke: PREVIEW_STROKE,
    fill: new Fill({ color: "rgba(255, 235, 59, 0.15)" }),
    image: new CircleStyle({
        radius: 8,
        fill: new Fill({ color: "#ffeb3b" }),
        stroke: new Stroke({ color: "#000", width: 2 }),
    }),
});

/** The corners of a drawn polygon, as whole blocks, without the closing one. */
function cornersOf(polygon: Polygon, geometry: MapGeometry): Points {
    const ring = polygon.getCoordinates()[0].slice(0, -1);
    return ring.map((c) => {
        const [x, z] = geometry.toBlocks(c);
        return [Math.round(x), Math.round(z)];
    });
}

function FactionOptions({ includeMe }: { includeMe: boolean }) {
    // Only rendered for admins: they can pick any faction still alive
    const { factions } = useFactions();
    return (
        <>
            {includeMe && <option value="">Moi</option>}
            {(factions ?? [])
                .filter((f) => !f.deleted_at)
                .map((f) => (
                    <option key={f.faction_id} value={f.faction_id}>
                        {f.name}
                    </option>
                ))}
        </>
    );
}

function FactionSelect({
    value,
    onChange,
    includeMe,
    isAdmin,
    ownFactionId,
    disabled,
}: {
    value: number | null;
    onChange: (id: number | null) => void;
    includeMe: boolean;
    isAdmin: boolean;
    ownFactionId: number | null;
    disabled?: boolean;
}) {
    return (
        <select
            value={value ?? ""}
            disabled={disabled}
            onChange={(e) =>
                onChange(e.target.value === "" ? null : Number(e.target.value))
            }
        >
            {isAdmin ? (
                <FactionOptions includeMe={includeMe} />
            ) : (
                <>
                    {includeMe && <option value="">Moi</option>}
                    {ownFactionId !== null && (
                        <option value={ownFactionId}>Ma faction</option>
                    )}
                </>
            )}
        </select>
    );
}

export default function MapEditor({
    folder,
    map,
    geometry,
    territories,
    markers,
    selection,
    onCloseSelection,
    busyRef,
    pickRef,
    onRefresh,
    onChanged,
    leading,
}: {
    folder: string;
    map: OlMap;
    geometry: MapGeometry;
    territories: TerritoryType[];
    markers: MarkerType[];
    selection: Selection | null;
    onCloseSelection: () => void;
    busyRef: MutableRefObject<boolean>;
    pickRef: MutableRefObject<((block: [number, number]) => void) | null>;
    /** Read the overlay again, keeping the selection. */
    onRefresh: () => void;
    /** Read it again after a change that ends the selection. */
    onChanged: () => void;
    /** Shown first in the toolbar (the "go to" control of the viewer). */
    leading?: ReactNode;
}) {
    const selected = selection?.entity ?? null;
    const rights = useMapRights();
    const [draft, setDraft] = useState<Draft | null>(null);
    // The outline being edited: replaced on load and redraw, never on a
    // modification (the Modify interaction owns it then).
    const [shape, setShape] = useState<{ points: Points } | null>(null);
    const [drawing, setDrawing] = useState(false);
    const [error, setError] = useState("");
    const [saving, setSaving] = useState(false);
    const pointsRef = useRef<Points>([]);

    const isAdmin = rights.isAdmin;
    // One spawn per map, and only an admin sets it
    const spawnExists = markers.some((m) => m.kind === "spawn");
    const canDraw = rights.loggedIn && (isAdmin || rights.factionId !== null);

    const territory =
        selected?.type === "territory"
            ? (territories.find((t) => t.territory_id === selected.id) ?? null)
            : null;
    const marker =
        selected?.type === "marker"
            ? (markers.find((m) => m.marker_id === selected.id) ?? null)
            : null;

    // While something is being edited the map does not change the selection
    const editing = draft !== null;
    useEffect(() => {
        busyRef.current = editing;
        return () => {
            busyRef.current = false;
        };
    }, [editing, busyRef]);

    // The outline: drawing it, then moving its corners
    useEffect(() => {
        const source = new VectorSource();
        const layer = new VectorLayer({
            source,
            zIndex: 60,
            style: PREVIEW_STYLE,
        });
        map.addLayer(layer);
        const cleanups: (() => void)[] = [() => map.removeLayer(layer)];

        if (drawing) {
            const draw = new Draw({ type: "Polygon", style: PREVIEW_STYLE });
            draw.on("drawend", (event) => {
                const polygon = event.feature.getGeometry() as Polygon;
                const points = cornersOf(polygon, geometry);
                pointsRef.current = points;
                setShape({ points });
                setDrawing(false);
            });
            map.addInteraction(draw);
            cleanups.push(() => map.removeInteraction(draw));
        } else if (shape) {
            const ring = shape.points.map((p) => geometry.toView(p));
            ring.push(ring[0]);
            const feature = new Feature(new Polygon([ring]));
            source.addFeature(feature);
            const modify = new Modify({ source });
            modify.on("modifyend", () => {
                pointsRef.current = cornersOf(
                    feature.getGeometry() as Polygon,
                    geometry,
                );
            });
            map.addInteraction(modify);
            cleanups.push(() => map.removeInteraction(modify));
        }
        return () => cleanups.forEach((fn) => fn());
    }, [map, geometry, shape, drawing]);

    // The point being placed
    const markerX = draft?.kind === "marker" ? draft.x : "";
    const markerZ = draft?.kind === "marker" ? draft.z : "";
    useEffect(() => {
        const x = Number(markerX);
        const z = Number(markerZ);
        if (markerX.trim() === "" || markerZ.trim() === "") return;
        if (!Number.isFinite(x) || !Number.isFinite(z)) return;
        const source = new VectorSource({
            features: [new Feature(new Point(geometry.toView([x, z])))],
        });
        const layer = new VectorLayer({
            source,
            zIndex: 61,
            style: PREVIEW_STYLE,
        });
        map.addLayer(layer);
        return () => {
            map.removeLayer(layer);
        };
    }, [map, geometry, markerX, markerZ]);

    // Stop picking when the form closes
    useEffect(
        () => () => {
            pickRef.current = null;
        },
        [pickRef],
    );

    function close() {
        pickRef.current = null;
        setDraft(null);
        setShape(null);
        setDrawing(false);
        setError("");
        setSaving(false);
    }

    function newTerritory() {
        const factionId = isAdmin ? null : rights.factionId;
        close();
        pointsRef.current = [];
        setDraft({
            kind: "territory",
            id: null,
            name: "",
            description: "",
            color: factionColor(factionId ?? 0),
            factionId,
        });
    }

    function editTerritory(t: TerritoryType) {
        close();
        pointsRef.current = t.points;
        setShape({ points: t.points });
        setDraft({
            kind: "territory",
            id: t.territory_id,
            name: t.name,
            description: t.description ?? "",
            color: factionColor(t.faction_id, t.color),
            factionId: t.faction_id,
        });
    }

    function newMarker(markerKind: MarkerKind = "generic") {
        close();
        setDraft({
            kind: "marker",
            id: null,
            label: markerKind === "spawn" ? MARKER_KINDS.spawn : "",
            description: "",
            markerKind,
            x: "",
            z: "",
            color: "",
            factionId: null,
        });
    }

    function editMarker(m: MarkerType) {
        close();
        setDraft({
            kind: "marker",
            id: m.marker_id,
            label: m.label,
            description: m.description ?? "",
            markerKind: m.kind,
            x: String(m.x),
            z: String(m.z),
            color: m.color ?? "",
            factionId: m.faction_id,
        });
    }

    // While a point's form is open, a click on the map moves it there
    const placing = draft?.kind === "marker";
    useEffect(() => {
        if (!placing) return;
        pickRef.current = ([x, z]) =>
            setDraft((d) =>
                d && d.kind === "marker"
                    ? {
                          ...d,
                          x: String(Math.round(x)),
                          z: String(Math.round(z)),
                      }
                    : d,
            );
        const target = map.getTargetElement();
        target?.classList.add("map-picking");
        return () => {
            pickRef.current = null;
            target?.classList.remove("map-picking");
        };
    }, [placing, map, pickRef]);

    /** The kinds a point's form offers. */
    function kindChoices(d: MarkerDraft): MarkerKind[] {
        return (Object.keys(MARKER_KINDS) as MarkerKind[]).filter(
            (key) =>
                // One spawn per map, placed by an admin
                (key !== "spawn" ||
                    d.markerKind === "spawn" ||
                    (isAdmin && !spawnExists)) &&
                // A point cannot become a station: a station is made new
                (key !== "station" || d.id === null),
        );
    }

    async function save() {
        if (!draft) return;
        setError("");
        setSaving(true);
        try {
            if (draft.kind === "territory") {
                const points = pointsRef.current;
                if (points.length < 3) {
                    setError("Tracez d'abord le contour (3 points au moins).");
                    return;
                }
                if (draft.id === null && draft.factionId === null) {
                    setError("Choisissez une faction.");
                    return;
                }
                const body = {
                    name: draft.name,
                    description: draft.description.trim() || null,
                    color: draft.color,
                    points,
                };
                if (draft.id === null) {
                    await axios.post("/map/territories", {
                        ...body,
                        map_name: folder,
                        faction_id: draft.factionId,
                    });
                } else {
                    await axios.put(`/map/territories/${draft.id}`, body);
                }
            } else {
                const x = Number(draft.x);
                const z = Number(draft.z);
                if (
                    draft.x.trim() === "" ||
                    draft.z.trim() === "" ||
                    !Number.isInteger(x) ||
                    !Number.isInteger(z)
                ) {
                    setError("X et Z doivent être des nombres entiers.");
                    return;
                }
                if (draft.markerKind === "station") {
                    // A station is a real station, listed on the stations
                    // page like one made there (the map shows those).
                    await axios.post("/stations", {
                        name: draft.label,
                        description: draft.description.trim() || null,
                        x,
                        z,
                        dimension: dimensionOfFolder(folder),
                    });
                    close();
                    onChanged();
                    return;
                }
                const color =
                    draft.markerKind === "generic" && draft.color.trim() !== ""
                        ? normalizeHex(draft.color)
                        : null;
                if (
                    color === null &&
                    draft.markerKind === "generic" &&
                    draft.color.trim() !== ""
                ) {
                    setError("La couleur doit ressembler à #1a2b3c.");
                    return;
                }
                const body = {
                    label: draft.label,
                    description: draft.description.trim() || null,
                    kind: draft.markerKind,
                    x,
                    z,
                    color,
                };
                if (draft.id === null) {
                    await axios.post("/map/markers", {
                        ...body,
                        map_name: folder,
                        ...(draft.factionId !== null
                            ? { faction_id: draft.factionId }
                            : {}),
                    });
                } else {
                    await axios.put(`/map/markers/${draft.id}`, body);
                }
            }
            close();
            onChanged();
        } catch (err) {
            setError(getErrorMessage(err, "Enregistrement impossible"));
        } finally {
            setSaving(false);
        }
    }

    async function toggleExplored(m: MarkerType) {
        setError("");
        try {
            await axios.put(`/map/markers/${m.marker_id}/explored`, {
                explored: !m.explored,
            });
            onRefresh(); // the card stays open and shows the new state
        } catch (err) {
            setError(getErrorMessage(err, "Modification impossible"));
        }
    }

    async function remove(entity: EntityRef, name: string) {
        if (!window.confirm(`Supprimer « ${name} » ?`)) return;
        setError("");
        try {
            await axios.delete(
                entity.type === "territory"
                    ? `/map/territories/${entity.id}`
                    : `/map/markers/${entity.id}`,
            );
            close();
            onChanged();
        } catch (err) {
            setError(getErrorMessage(err, "Suppression impossible"));
        }
    }

    const editable =
        !draft &&
        ((territory !== null && rights.canEditTerritory(territory)) ||
            (marker !== null && rights.canEditMarker(marker)));
    const explorable =
        marker !== null &&
        isStructure(marker.kind) &&
        rights.canMarkExplored(marker);

    const tools = rights.loading ? (
        <div className="map-float map-tools">{leading}</div>
    ) : !rights.loggedIn ? (
        <div className="map-float map-tools">
            {leading}
            <p className="map-hint">
                <Link to="/login">Connectez-vous</Link> pour ajouter vos points.
            </p>
        </div>
    ) : draft ? (
        <div className="map-float map-tools">{leading}</div>
    ) : (
        <div className="map-float map-tools" role="toolbar">
            {leading}
            <button
                type="button"
                className="button"
                title="Ajouter un point d'intérêt ou une gare"
                onClick={() => newMarker()}
            >
                ＋ Point
            </button>
            {canDraw && (
                <button
                    type="button"
                    className="button"
                    title="Dessiner le territoire d'une faction"
                    onClick={newTerritory}
                >
                    ＋ Territoire
                </button>
            )}
            {isAdmin && !spawnExists && (
                <button
                    type="button"
                    className="button"
                    onClick={() => newMarker("spawn")}
                >
                    ＋ Spawn
                </button>
            )}
        </div>
    );

    const card = !draft && selection && (
        <div className="map-float map-card" aria-live="polite">
            <div className="map-card-header">
                {marker?.kind === "generic" && marker.color ? (
                    <span
                        className="map-card-dot"
                        style={{ background: marker.color }}
                    />
                ) : (
                    selection.iconKind && (
                        <img
                            className="map-kind-icon map-card-icon"
                            src={iconUrl(selection.iconKind)}
                            alt=""
                        />
                    )
                )}
                <div className="map-card-title">
                    <h3>{selection.title}</h3>
                    <p className="map-selection-kind">{selection.kind}</p>
                </div>
                <button
                    type="button"
                    className="map-close"
                    aria-label="Fermer"
                    onClick={onCloseSelection}
                >
                    ×
                </button>
            </div>

            {selection.lines.map((line, i) => (
                <p key={i}>{line}</p>
            ))}

            {marker && isStructure(marker.kind) && (
                <p className={`map-explored${marker.explored ? " done" : ""}`}>
                    {marker.explored
                        ? `Explorée${
                              marker.explored_by_name
                                  ? ` par ${marker.explored_by_name}`
                                  : ""
                          }${
                              marker.explored_at
                                  ? ` le ${new Date(
                                        marker.explored_at,
                                    ).toLocaleDateString("fr-FR")}`
                                  : ""
                          } : les ressources ont été récupérées.`
                        : "Pas encore explorée : les ressources sont sur place."}
                </p>
            )}

            {selection.stationId !== null && (
                <p>
                    <Link to={`/station/${selection.stationId}`}>
                        Voir la fiche de la gare →
                    </Link>
                </p>
            )}

            {(editable || explorable) && (
                <div className="map-editor-actions">
                    {explorable && marker && (
                        <button
                            type="button"
                            className="button"
                            aria-pressed={marker.explored}
                            onClick={() => void toggleExplored(marker)}
                        >
                            {marker.explored
                                ? "Annuler « exploré »"
                                : "✓ Marquer exploré"}
                        </button>
                    )}
                    {territory && rights.canEditTerritory(territory) && (
                        <>
                            <button
                                type="button"
                                className="button"
                                onClick={() => editTerritory(territory)}
                            >
                                Modifier
                            </button>
                            <button
                                type="button"
                                className="button map-danger"
                                onClick={() =>
                                    remove(
                                        {
                                            type: "territory",
                                            id: territory.territory_id,
                                        },
                                        territory.name,
                                    )
                                }
                            >
                                Supprimer
                            </button>
                        </>
                    )}
                    {marker && rights.canEditMarker(marker) && (
                        <>
                            <button
                                type="button"
                                className="button"
                                onClick={() => editMarker(marker)}
                            >
                                Modifier
                            </button>
                            <button
                                type="button"
                                className="button map-danger"
                                onClick={() =>
                                    remove(
                                        {
                                            type: "marker",
                                            id: marker.marker_id,
                                        },
                                        marker.label,
                                    )
                                }
                            >
                                Supprimer
                            </button>
                        </>
                    )}
                </div>
            )}
        </div>
    );

    const drawerHeader = (title: string) => (
        <div className="map-card-header">
            <div className="map-card-title">
                <h3>{title}</h3>
            </div>
            <button
                type="button"
                className="map-close"
                aria-label="Annuler"
                onClick={close}
            >
                ×
            </button>
        </div>
    );

    const errorLine = error && (
        <p className="map-error" role="alert">
            {error}
        </p>
    );

    return (
        <>
            {tools}
            {card}
            {!draft && !selection && errorLine}

            {draft?.kind === "territory" && (
                <form
                    className="map-float map-drawer map-editor-form"
                    onSubmit={(e) => {
                        e.preventDefault();
                        void save();
                    }}
                >
                    {drawerHeader(
                        draft.id === null
                            ? "Nouveau territoire"
                            : "Modifier le territoire",
                    )}
                    <label>
                        Nom
                        <input
                            type="text"
                            required
                            maxLength={80}
                            value={draft.name}
                            onChange={(e) =>
                                setDraft({ ...draft, name: e.target.value })
                            }
                        />
                    </label>
                    {draft.id === null && (
                        <label>
                            Faction
                            <FactionSelect
                                value={draft.factionId}
                                includeMe={false}
                                isAdmin={isAdmin}
                                ownFactionId={rights.factionId}
                                onChange={(id) =>
                                    setDraft({
                                        ...draft,
                                        factionId: id,
                                        color: factionColor(id ?? 0),
                                    })
                                }
                            />
                        </label>
                    )}
                    <div className="map-form-row">
                        <label className="map-grow">
                            Description
                            <textarea
                                rows={2}
                                value={draft.description}
                                onChange={(e) =>
                                    setDraft({
                                        ...draft,
                                        description: e.target.value,
                                    })
                                }
                            />
                        </label>
                        <label>
                            Couleur
                            <input
                                type="color"
                                value={draft.color}
                                onChange={(e) =>
                                    setDraft({
                                        ...draft,
                                        color: e.target.value,
                                    })
                                }
                            />
                        </label>
                    </div>

                    <div className="map-step">
                        <strong>Contour</strong>
                        {drawing ? (
                            <p className="map-hint">
                                Cliquez sur la carte pour poser les coins,
                                double-cliquez pour terminer.
                            </p>
                        ) : shape ? (
                            <p className="map-hint">
                                {shape.points.length} coins. Glissez les coins
                                jaunes pour ajuster.
                            </p>
                        ) : (
                            <p className="map-hint">Pas encore tracé.</p>
                        )}
                        <button
                            type="button"
                            className="button"
                            disabled={drawing}
                            onClick={() => {
                                pointsRef.current = [];
                                setShape(null);
                                setDrawing(true);
                            }}
                        >
                            {shape ? "Redessiner" : "Tracer le contour"}
                        </button>
                    </div>

                    {errorLine}
                    <div className="map-editor-actions map-form-actions">
                        <button
                            type="submit"
                            className="button map-primary"
                            disabled={saving || drawing}
                        >
                            Enregistrer
                        </button>
                        <button
                            type="button"
                            className="button"
                            onClick={close}
                        >
                            Annuler
                        </button>
                    </div>
                </form>
            )}

            {draft?.kind === "marker" && (
                <form
                    className="map-float map-drawer map-editor-form"
                    onSubmit={(e) => {
                        e.preventDefault();
                        void save();
                    }}
                >
                    {drawerHeader(
                        draft.id === null
                            ? "Nouveau point"
                            : "Modifier le point",
                    )}

                    {/* The spawn stays the spawn (delete it to remove it):
                        its position is what changes */}
                    {draft.id !== null && draft.markerKind === "spawn" ? (
                        <p className="map-kind-fixed">
                            <img
                                className="map-kind-icon"
                                src={iconUrl("spawn")}
                                alt=""
                            />
                            {MARKER_KINDS.spawn}
                        </p>
                    ) : (
                        <fieldset className="map-kind-grid">
                            <legend>Type</legend>
                            {kindChoices(draft).map((key) => (
                                <label
                                    key={key}
                                    className="map-kind-option"
                                    title={MARKER_KINDS[key]}
                                >
                                    <input
                                        type="radio"
                                        name="marker-kind"
                                        value={key}
                                        checked={draft.markerKind === key}
                                        onChange={() =>
                                            setDraft({
                                                ...draft,
                                                markerKind: key,
                                                factionId:
                                                    key === "spawn"
                                                        ? null
                                                        : draft.factionId,
                                            })
                                        }
                                    />
                                    <img
                                        className="map-kind-icon"
                                        src={iconUrl(key)}
                                        alt=""
                                    />
                                    <span>{MARKER_KINDS[key]}</span>
                                </label>
                            ))}
                        </fieldset>
                    )}

                    <label>
                        Nom
                        <input
                            type="text"
                            required
                            maxLength={60}
                            placeholder={
                                draft.markerKind === "station"
                                    ? "Gare du Nord"
                                    : MARKER_KINDS[draft.markerKind]
                            }
                            value={draft.label}
                            onChange={(e) =>
                                setDraft({ ...draft, label: e.target.value })
                            }
                        />
                    </label>
                    {draft.id === null &&
                        draft.markerKind !== "spawn" &&
                        draft.markerKind !== "station" && (
                            <label>
                                Appartient à
                                <FactionSelect
                                    value={draft.factionId}
                                    includeMe
                                    isAdmin={isAdmin}
                                    ownFactionId={rights.factionId}
                                    onChange={(id) =>
                                        setDraft({ ...draft, factionId: id })
                                    }
                                />
                            </label>
                        )}
                    {draft.markerKind === "generic" && (
                        <ColorField
                            value={draft.color}
                            onChange={(color) => setDraft({ ...draft, color })}
                        />
                    )}
                    <label>
                        Description
                        <textarea
                            rows={2}
                            placeholder="Facultatif"
                            value={draft.description}
                            onChange={(e) =>
                                setDraft({
                                    ...draft,
                                    description: e.target.value,
                                })
                            }
                        />
                    </label>

                    <div className="map-step">
                        <strong>Position</strong>
                        <p className="map-hint">
                            Cliquez sur la carte pour placer le point, ou tapez
                            ses coordonnées.
                        </p>
                        <div className="map-coords">
                            <label>
                                X
                                <input
                                    type="text"
                                    inputMode="numeric"
                                    required
                                    value={draft.x}
                                    onChange={(e) =>
                                        setDraft({
                                            ...draft,
                                            x: e.target.value,
                                        })
                                    }
                                />
                            </label>
                            <label>
                                Z
                                <input
                                    type="text"
                                    inputMode="numeric"
                                    required
                                    value={draft.z}
                                    onChange={(e) =>
                                        setDraft({
                                            ...draft,
                                            z: e.target.value,
                                        })
                                    }
                                />
                            </label>
                        </div>
                    </div>

                    {draft.markerKind === "station" && (
                        <p className="map-hint">
                            La gare rejoindra la liste des gares, où vous
                            pourrez ajouter ses quais.
                        </p>
                    )}

                    {errorLine}
                    <div className="map-editor-actions map-form-actions">
                        <button
                            type="submit"
                            className="button map-primary"
                            disabled={saving}
                        >
                            Enregistrer
                        </button>
                        <button
                            type="button"
                            className="button"
                            onClick={close}
                        >
                            Annuler
                        </button>
                    </div>
                </form>
            )}
        </>
    );
}
