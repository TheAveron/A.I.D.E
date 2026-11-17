import { Link, useParams } from "react-router";

import { useTrain, useTrainHistory } from "../../hooks/network/trains";
import { useTrainRights } from "../../hooks/network/trainrights";
import TrainBoard from "../../components/network/train_board";
import TrainEditor from "../../components/network/train_editor";
import TrainOwner from "../../components/network/train_owner";
import Username from "../../components/users/username";

const ACTIONS = {
    CREATED: "Enregistré",
    UPDATED: "Modifié",
    RETIRED: "Retiré",
} as const;

/** One train: its name, owner, history, and (for those who may) its editor. */
export default function TrainPage() {
    const { trainid } = useParams();
    const { train, loading, error, refresh } = useTrain(trainid);
    const { history, refresh: refreshHistory } = useTrainHistory(trainid);
    const rights = useTrainRights();

    if (error) return <p role="alert">{error}</p>;
    if (loading || !train) return <p>Chargement...</p>;

    const changed = () => {
        refresh();
        refreshHistory();
    };

    return (
        <div className="information-container">
            <div className="snippet-container">
                <h2>{train.display_name}</h2>
                <TrainBoard
                    name={train.display_name}
                    line={train.line}
                    service={train.service}
                    number={train.number}
                />
                <ul>
                    <li>
                        Ligne :{" "}
                        <Link to={`/line/${train.line}`}>{train.line}</Link>
                    </li>
                    {train.legacy_id && <li>Ancien nom : {train.legacy_id}</li>}
                    <li>
                        Propriétaire : <TrainOwner train={train} />
                    </li>
                    <li>
                        Enregistré le{" "}
                        {new Date(train.created_at).toLocaleDateString()}
                    </li>
                    {train.retired_at && (
                        <li>
                            Retiré le{" "}
                            {new Date(train.retired_at).toLocaleDateString()}
                        </li>
                    )}
                </ul>
                <Link className="button" to="/trains">
                    Tous les trains
                </Link>
            </div>

            <div className="snippet-container">
                <h2>Historique</h2>
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Événement</th>
                                <th>Ancien nom</th>
                                <th>Nouveau nom</th>
                                <th>Par</th>
                            </tr>
                        </thead>
                        <tbody>
                            {history.map((h) => (
                                <tr key={h.history_id}>
                                    <td>
                                        {new Date(
                                            h.created_at,
                                        ).toLocaleString()}
                                    </td>
                                    <td>{ACTIONS[h.action]}</td>
                                    <td>{h.old_name ?? "-"}</td>
                                    <td>{h.new_name ?? "-"}</td>
                                    <td>
                                        {h.actor_user_id ? (
                                            <Username
                                                userId={String(h.actor_user_id)}
                                            />
                                        ) : (
                                            "-"
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {rights.user && !train.retired_at && rights.canManage(train) && (
                <TrainEditor
                    key={`${train.train_id}-${train.updated_at}`}
                    train={train}
                    userId={rights.user.user_id}
                    factionId={rights.factionId}
                    isTrainAdmin={rights.isTrainAdmin}
                    onChanged={changed}
                />
            )}
        </div>
    );
}
