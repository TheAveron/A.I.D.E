import { Link, useParams } from "react-router";

import { useLines } from "../components/hooks/trains";
import { useStation } from "../components/hooks/stations";
import { useTrainRights } from "../components/hooks/trainrights";
import PlatformsPanel from "../components/snippets/platforms_panel";
import StationEditor from "../components/snippets/station_editor";
import Username from "../components/snippets/username";
import { DIMENSIONS } from "../types/trains";

/** One station: place, platforms, the lines that serve it. */
export default function StationPage() {
    const { stationid } = useParams();
    const { station, loading, error, refresh } = useStation(stationid);
    const { lines } = useLines();
    const rights = useTrainRights();

    if (error) return <p role="alert">{error}</p>;
    if (loading || !station) return <p>Chargement...</p>;

    const canManage =
        rights.isTrainAdmin ||
        (!!rights.user && station.created_by_user_id === rights.user.user_id);
    const serving = lines.filter((l) =>
        l.stops.some((s) => s.station.station_id === station.station_id),
    );

    return (
        <div className="information-container">
            <div className="snippet-container">
                <h2>{station.name}</h2>
                <ul>
                    <li>
                        Position : X {station.x}
                        {station.y !== null && `, Y ${station.y}`}, Z{" "}
                        {station.z} ({DIMENSIONS[station.dimension]})
                    </li>
                    {station.description && <li>{station.description}</li>}
                    <li>
                        Lignes :{" "}
                        {serving.length === 0
                            ? "aucune"
                            : serving.map((l, i) => (
                                  <span key={l.code}>
                                      {i > 0 && ", "}
                                      <Link to={`/line/${l.code}`}>
                                          {l.code}
                                      </Link>
                                  </span>
                              ))}
                    </li>
                    {station.created_by_user_id && (
                        <li>
                            Enregistrée par{" "}
                            <Username
                                userId={String(station.created_by_user_id)}
                            />
                        </li>
                    )}
                </ul>
                <Link className="button" to="/stations">
                    Toutes les gares
                </Link>
            </div>

            <PlatformsPanel
                stationId={station.station_id}
                platforms={station.platforms}
                canManage={canManage}
                onChanged={refresh}
            />

            {canManage && (
                <StationEditor
                    key={station.updated_at}
                    station={station}
                    onChanged={refresh}
                />
            )}
        </div>
    );
}
