import axios from "axios";
import { useEffect, useRef, useState } from "react";
import type { MutableRefObject } from "react";
import type OlMap from "ol/Map";
import Feature from "ol/Feature";
import Draw from "ol/interaction/Draw";
import Modify from "ol/interaction/Modify";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import { Point, Polygon } from "ol/geom";
import { Circle as CircleStyle, Fill, Stroke, Style } from "ol/style";

import { MARKER_KINDS } from "../../types/map";
import type { MarkerKind, MarkerType, TerritoryType } from "../../types/map";
import { getErrorMessage } from "../../utils/apierror";
import { factionColor } from "../../utils/mapcolors";
import { iconUrl } from "../../utils/mapicons";
import type { MapGeometry } from "../../utils/unmined";
import { useFactions } from "../hooks/factions";
import { useMapRights } from "../hooks/maprights";

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
    // null: the player's own point; otherwise a faction's
    factionId: number | null;
}

type Draft = TerritoryDraft | MarkerDraft;

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
    selected,
    busyRef,
    pickRef,
    onChanged,
}: {
    folder: string;
    map: OlMap;
    geometry: MapGeometry;
    territories: TerritoryType[];
    markers: MarkerType[];
    selected: EntityRef | null;
    busyRef: MutableRefObject<boolean>;
    pickRef: MutableRefObject<((block: [number, number]) => void) | null>;
    onChanged: () => void;
}) {
    const rights = useMapRights();
    const [draft, setDraft] = useState<Draft | null>(null);
    // The outline being edited: replaced on load and redraw, never on a
    // modification (the Modify interaction owns it then).
    const [shape, setShape] = useState<{ points: Points } | null>(null);
    const [drawing, setDrawing] = useState(false);
    const [picking, setPicking] = useState(false);
    const [error, setError] = useState("");
    const [saving, setSaving] = useState(false);
    const pointsRef = useRef<Points>([]);

    const isAdmin = rights.isAdmin;
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
        setPicking(false);
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

    function newMarker() {
        close();
        setDraft({
            kind: "marker",
            id: null,
            label: "",
            description: "",
            markerKind: "generic",
            x: "",
            z: "",
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
            factionId: m.faction_id,
        });
    }

    function pickOnMap() {
        setPicking(true);
        pickRef.current = ([x, z]) => {
            setPicking(false);
            setDraft((d) =>
                d && d.kind === "marker"
                    ? {
                          ...d,
                          x: String(Math.round(x)),
                          z: String(Math.round(z)),
                      }
                    : d,
            );
        };
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
                const body = {
                    label: draft.label,
                    description: draft.description.trim() || null,
                    kind: draft.markerKind,
                    x,
                    z,
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

    if (rights.loading) return null;
    if (!rights.loggedIn) {
        return (
            <p className="map-hint">
                Connectez-vous pour ajouter vos points sur la carte.
            </p>
        );
    }

    const editable =
        !draft &&
        ((territory && rights.canEditTerritory(territory)) ||
            (marker && rights.canEditMarker(marker)));

    return (
        <div className="map-editor">
            <h3>Édition</h3>

            {!draft && (
                <div className="map-editor-actions">
                    {canDraw && (
                        <button
                            type="button"
                            className="button"
                            onClick={newTerritory}
                        >
                            Nouveau territoire
                        </button>
                    )}
                    <button
                        type="button"
                        className="button"
                        onClick={newMarker}
                    >
                        Nouveau point
                    </button>
                </div>
            )}

            {editable && (
                <div className="map-editor-actions">
                    {territory && (
                        <>
                            <button
                                type="button"
                                className="button"
                                onClick={() => editTerritory(territory)}
                            >
                                Modifier « {territory.name} »
                            </button>
                            <button
                                type="button"
                                className="button"
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
                    {marker && (
                        <>
                            <button
                                type="button"
                                className="button"
                                onClick={() => editMarker(marker)}
                            >
                                Modifier « {marker.label} »
                            </button>
                            <button
                                type="button"
                                className="button"
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

            {draft?.kind === "territory" && (
                <form
                    className="map-editor-form"
                    onSubmit={(e) => {
                        e.preventDefault();
                        void save();
                    }}
                >
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
                    <label>
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
                                setDraft({ ...draft, color: e.target.value })
                            }
                        />
                    </label>

                    {drawing ? (
                        <p className="map-hint">
                            Cliquez pour poser les coins, double-clic pour
                            terminer.
                        </p>
                    ) : shape ? (
                        <p className="map-hint">
                            {shape.points.length} coins. Glissez les coins
                            jaunes pour ajuster le contour.
                        </p>
                    ) : (
                        <p className="map-hint">Contour pas encore tracé.</p>
                    )}
                    <div className="map-editor-actions">
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
                        <button
                            type="submit"
                            className="button"
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
                    className="map-editor-form"
                    onSubmit={(e) => {
                        e.preventDefault();
                        void save();
                    }}
                >
                    <label>
                        Nom
                        <input
                            type="text"
                            required
                            maxLength={60}
                            value={draft.label}
                            onChange={(e) =>
                                setDraft({ ...draft, label: e.target.value })
                            }
                        />
                    </label>
                    <label>
                        Type
                        <span className="map-kind-select">
                            <img
                                className="map-kind-icon"
                                src={iconUrl(draft.markerKind)}
                                alt=""
                            />
                            <select
                                value={draft.markerKind}
                                onChange={(e) =>
                                    setDraft({
                                        ...draft,
                                        markerKind: e.target
                                            .value as MarkerKind,
                                    })
                                }
                            >
                                {(
                                    Object.entries(MARKER_KINDS) as [
                                        MarkerKind,
                                        string,
                                    ][]
                                ).map(([key, label]) => (
                                    <option key={key} value={key}>
                                        {label}
                                    </option>
                                ))}
                            </select>
                        </span>
                    </label>
                    {draft.id === null && (
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
                    <label>
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
                    <div className="map-goto">
                        <input
                            type="text"
                            inputMode="numeric"
                            placeholder="X"
                            aria-label="X"
                            value={draft.x}
                            onChange={(e) =>
                                setDraft({ ...draft, x: e.target.value })
                            }
                        />
                        <input
                            type="text"
                            inputMode="numeric"
                            placeholder="Z"
                            aria-label="Z"
                            value={draft.z}
                            onChange={(e) =>
                                setDraft({ ...draft, z: e.target.value })
                            }
                        />
                    </div>
                    {picking && (
                        <p className="map-hint">Cliquez sur la carte...</p>
                    )}
                    <div className="map-editor-actions">
                        <button
                            type="button"
                            className="button"
                            onClick={pickOnMap}
                        >
                            Choisir sur la carte
                        </button>
                        <button
                            type="submit"
                            className="button"
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

            {error && (
                <p className="map-error" role="alert">
                    {error}
                </p>
            )}
        </div>
    );
}
