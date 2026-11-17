import { Link, useParams } from "react-router";

import { useLines, useTrains } from "../../hooks/network/trains";
import { useTrainRights } from "../../hooks/network/trainrights";
import LineEditor from "../../components/network/line_editor";
import LineStopsEditor from "../../components/network/line_stops_editor";
import LineSwatch from "../../components/network/line_swatch";
import { MAINTENANCE_LINE, SERVICE_NAMES } from "../../utils/trains";
import Factionname from "../../components/factions/factionname";

/** One line: its stations in order, its trains, and its editors. */
export default function LinePage() {
    const { code } = useParams();
    const { lines, loading, error, refresh } = useLines();
    const { trains } = useTrains({ line: code }, !!code);
    const rights = useTrainRights();

    if (error) return <p role="alert">{error}</p>;
    if (loading) return <p>Chargement...</p>;

    const line = lines.find((l) => l.code === code?.toUpperCase());
    if (!line) {
        return (
            <div className="information-container">
                <div className="snippet-container">
                    <p>Cette ligne n&apos;existe pas.</p>
                    <Link className="button" to="/lines">
                        Toutes les lignes
                    </Link>
                </div>
            </div>
        );
    }

    const isMaintenance = line.code === MAINTENANCE_LINE;
    const canManage =
        !isMaintenance &&
        (rights.isTrainAdmin ||
            (line.owner_faction_id !== null &&
                line.owner_faction_id === rights.factionId));

    return (
        <div className="information-container">
            <div className="snippet-container">
                <h2>
                    <LineSwatch code={line.code} color={line.color} />
                    {line.name ? ` - ${line.name}` : ""}
                </h2>
                {line.description && <p>{line.description}</p>}
                {line.owner_faction_id && (
                    <p>
                        Gérée par{" "}
                        <Link to={`/faction/${line.owner_faction_id}`}>
                            <Factionname
                                factionId={String(line.owner_faction_id)}
                            />
                        </Link>
                    </p>
                )}
                <Link className="button" to="/lines">
                    Toutes les lignes
                </Link>
            </div>

            {!isMaintenance && (
                <LineStopsEditor
                    key={line.stops.map((s) => s.station.station_id).join(",")}
                    code={line.code}
                    stops={line.stops.map((s) => s.station)}
                    canManage={canManage}
                    onChanged={refresh}
                />
            )}

            <div className="snippet-container">
                <h2>Trains de la ligne</h2>
                {trains.length === 0 ? (
                    <p className="empty-state">Aucun train en service.</p>
                ) : (
                    <ul>
                        {trains.map((t) => (
                            <li key={t.train_id}>
                                <Link to={`/train/${t.train_id}`}>
                                    {t.display_name}
                                </Link>
                                {t.service && (
                                    <small> ({SERVICE_NAMES[t.service]})</small>
                                )}
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            {canManage && <LineEditor line={line} onChanged={refresh} />}
        </div>
    );
}
