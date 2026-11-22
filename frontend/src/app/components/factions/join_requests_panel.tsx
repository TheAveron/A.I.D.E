import {
    useJoinRequestActions,
    useFactionJoinRequests,
} from "../../hooks/factions/joinrequests";
import { useMembers } from "../../hooks/factions/factionmembers";
import { useMemberCounts } from "../../hooks/factions/member_counts";
import { Link } from "react-router";

/**
 * Pending requests to join a faction, for the members who handle members:
 * accepting one makes the applicant a member ("Membre") of the faction.
 */
export default function JoinRequestsPanel({
    factionId,
}: {
    factionId: string;
}) {
    const { requests, loading, error, refresh } =
        useFactionJoinRequests(factionId);
    const {
        accept,
        refuse,
        loading: acting,
        error: actionError,
    } = useJoinRequestActions();
    const { refresh: refreshMembers } = useMembers(factionId);
    const { refresh: refreshCounts } = useMemberCounts();

    const decide = async (
        action: (id: number) => Promise<boolean>,
        requestId: number,
    ) => {
        if (await action(requestId)) {
            refresh();
            refreshMembers();
            refreshCounts();
        }
    };

    return (
        <div className="snippet-container">
            <h2>Demandes d'adhésion</h2>
            {error && <p role="alert">{error}</p>}
            {actionError && <p role="alert">{actionError}</p>}
            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Utilisateur</th>
                            <th>Message</th>
                            <th>Date</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr>
                                <td colSpan={4}>Chargement des demandes...</td>
                            </tr>
                        ) : requests.length === 0 ? (
                            <tr>
                                <td colSpan={4}>Aucune demande en attente.</td>
                            </tr>
                        ) : (
                            requests.map((request) => (
                                <tr key={request.request_id}>
                                    <td>
                                        <Link to={`/user/${request.user_id}`}>
                                            {request.username}
                                        </Link>
                                    </td>
                                    <td>{request.message ?? ""}</td>
                                    <td>
                                        {new Date(
                                            request.created_at,
                                        ).toLocaleDateString()}
                                    </td>
                                    <td>
                                        <button
                                            type="button"
                                            className="button"
                                            disabled={acting}
                                            onClick={() =>
                                                decide(
                                                    accept,
                                                    request.request_id,
                                                )
                                            }
                                        >
                                            Accepter
                                        </button>{" "}
                                        <button
                                            type="button"
                                            className="button"
                                            disabled={acting}
                                            onClick={() =>
                                                decide(
                                                    refuse,
                                                    request.request_id,
                                                )
                                            }
                                        >
                                            Refuser
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
