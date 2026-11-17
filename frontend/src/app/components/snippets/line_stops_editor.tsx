import axios from "axios";
import { useState } from "react";
import { Link } from "react-router";

import { useStations } from "../hooks/stations";
import { getErrorMessage } from "../../utils/apierror";
import type { LineStationType } from "../../types/trains";

/**
 * The stations of a line, in order: the first and the last are its ends.
 * Editable by those who may change the line, saved in one go.
 */
export default function LineStopsEditor({
    code,
    stops,
    canManage,
    onChanged,
}: {
    code: string;
    stops: LineStationType[];
    canManage: boolean;
    onChanged: () => void;
}) {
    const { stations } = useStations();
    // null: nothing edited, the stops of the line are shown as they are
    const [draft, setDraft] = useState<LineStationType[] | null>(null);
    const [toAdd, setToAdd] = useState("");
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState("");

    const shown = draft ?? stops;
    const available = stations.filter(
        (s) => !shown.some((t) => t.station_id === s.station_id),
    );

    const edit = (change: (list: LineStationType[]) => LineStationType[]) =>
        setDraft(change([...shown]));

    const move = (index: number, by: -1 | 1) =>
        edit((list) => {
            const target = index + by;
            if (target < 0 || target >= list.length) return list;
            [list[index], list[target]] = [list[target], list[index]];
            return list;
        });

    const add = () => {
        const station = stations.find((s) => String(s.station_id) === toAdd);
        if (!station) return;
        edit((list) => [...list, station]);
        setToAdd("");
    };

    const save = async () => {
        setBusy(true);
        setMessage("");
        try {
            await axios.put(`/lines/${code}/stops`, {
                station_ids: shown.map((s) => s.station_id),
            });
            setDraft(null);
            setMessage("✅ Gares enregistrées");
            onChanged();
        } catch (err) {
            setMessage(`❌ ${getErrorMessage(err)}`);
        } finally {
            setBusy(false);
        }
    };

    return (
        <div className="snippet-container">
            <h2>Gares de la ligne</h2>
            {shown.length === 0 ? (
                <p className="empty-state">Aucune gare sur cette ligne.</p>
            ) : (
                <ol>
                    {shown.map((s, i) => (
                        <li key={s.station_id}>
                            <Link to={`/station/${s.station_id}`}>
                                {s.name}
                            </Link>
                            {(i === 0 || i === shown.length - 1) &&
                                shown.length > 1 && <small> (terminus)</small>}
                            {canManage && (
                                <>
                                    {" "}
                                    <button
                                        type="button"
                                        className="button button-quiet icon-button"
                                        aria-label={`Monter ${s.name}`}
                                        disabled={i === 0}
                                        onClick={() => move(i, -1)}
                                    >
                                        <svg
                                            viewBox="0 0 24 24"
                                            strokeWidth="2"
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            aria-hidden="true"
                                        >
                                            <path d="m18 15-6-6-6 6" />
                                        </svg>
                                    </button>{" "}
                                    <button
                                        type="button"
                                        className="button button-quiet icon-button"
                                        aria-label={`Descendre ${s.name}`}
                                        disabled={i === shown.length - 1}
                                        onClick={() => move(i, 1)}
                                    >
                                        <svg
                                            viewBox="0 0 24 24"
                                            strokeWidth="2"
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            aria-hidden="true"
                                        >
                                            <path d="m6 9 6 6 6-6" />
                                        </svg>
                                    </button>{" "}
                                    <button
                                        type="button"
                                        className="button button-quiet"
                                        aria-label={`Retirer ${s.name}`}
                                        onClick={() =>
                                            edit((list) =>
                                                list.filter(
                                                    (t) =>
                                                        t.station_id !==
                                                        s.station_id,
                                                ),
                                            )
                                        }
                                    >
                                        Retirer
                                    </button>
                                </>
                            )}
                        </li>
                    ))}
                </ol>
            )}
            {canManage && (
                <>
                    <div className="toolbar">
                        <select
                            aria-label="Gare à ajouter"
                            value={toAdd}
                            onChange={(e) => setToAdd(e.target.value)}
                        >
                            <option value="">
                                Ajouter une gare à la fin...
                            </option>
                            {available.map((s) => (
                                <option key={s.station_id} value={s.station_id}>
                                    {s.name}
                                </option>
                            ))}
                        </select>
                        <button
                            type="button"
                            className="button"
                            disabled={toAdd === ""}
                            onClick={add}
                        >
                            Ajouter
                        </button>
                    </div>
                    <button
                        type="button"
                        className="button"
                        disabled={busy || draft === null}
                        onClick={save}
                    >
                        Enregistrer l&apos;ordre
                    </button>{" "}
                    {draft !== null && (
                        <button
                            type="button"
                            className="button"
                            disabled={busy}
                            onClick={() => setDraft(null)}
                        >
                            Annuler les changements
                        </button>
                    )}
                    <p>
                        <small>
                            Le premier et le dernier arrêt sont les deux
                            extrémités : c&apos;est là que s&apos;arrêtent les
                            express (E).
                        </small>
                    </p>
                </>
            )}
            {message && <p role="status">{message}</p>}
        </div>
    );
}
