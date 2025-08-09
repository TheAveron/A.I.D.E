import { useNavigate } from "react-router-dom";
import { useOfferHistoriesByActor } from "../hooks/offer_history";
import Username from "./username";
import Factionname from "./factionname";
import { Offername } from "./offername";
import { useMemo, useState } from "react";

export default function HistoryTable({
    factionId,
    HistoriesPerPage = 10,
}: {
    factionId?: string;
    HistoriesPerPage?: number;
}) {
    const navigate = useNavigate();

    const [page, setPage] = useState(1);

    const { offerHistories, loading, error } = useOfferHistoriesByActor({
        actorFactionId: factionId ?? null,
    });

    const sortedHistories = useMemo(() => {
        const copy = [...(offerHistories || [])];

        copy.sort(
            (a, b) =>
                new Date(b.timestamp).getTime() -
                new Date(a.timestamp).getTime()
        );

        return copy;
    }, [offerHistories]);

    const paginatedHistories = useMemo(() => {
        const start = (page - 1) * HistoriesPerPage;
        return sortedHistories.slice(start, start + HistoriesPerPage);
    }, [sortedHistories, page]);

    return (
        <div className="snippet-container history-container">
            <h2>Historique des offres</h2>
            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Nom</th>
                            <th>Action</th>
                            <th>Utilisateur</th>
                            <th>Notes</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {!error ? (
                            !loading ? (
                                paginatedHistories &&
                                paginatedHistories.length > 0 ? (
                                    paginatedHistories.map((offer) => (
                                        <tr key={offer.offer_id}>
                                            <td
                                                onClick={() => {
                                                    navigate(
                                                        "/A.I.D.E/user/" +
                                                            offer.offer_id
                                                    );
                                                }}
                                            >
                                                <Offername
                                                    offerId={offer.offer_id}
                                                />
                                            </td>
                                            <td>
                                                {offer.action.toLowerCase()}
                                            </td>
                                            <td>
                                                {!offer.actor_faction_id ? (
                                                    offer.actor_user_id ? (
                                                        <Username
                                                            userId={offer.actor_user_id.toString()}
                                                        />
                                                    ) : (
                                                        ""
                                                    )
                                                ) : (
                                                    <Factionname
                                                        factionId={offer.actor_faction_id.toString()}
                                                    />
                                                )}
                                            </td>
                                            <td>{offer.notes}</td>
                                            <td>
                                                {new Date(
                                                    offer.timestamp
                                                ).toLocaleDateString() +
                                                    ", " +
                                                    new Date(
                                                        offer.timestamp
                                                    ).toLocaleTimeString()}
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan={5}>
                                            Aucun utilisateur trouvé.
                                        </td>
                                    </tr>
                                )
                            ) : (
                                <tr>
                                    <td colSpan={5}>
                                        Chargement des membres...
                                    </td>
                                </tr>
                            )
                        ) : (
                            <tr>
                                <td colSpan={5}>{error}</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
            {sortedHistories.length > HistoriesPerPage && (
                <div className="pagination-controls">
                    <button
                        onClick={() => setPage((p) => Math.max(p - 1, 1))}
                        disabled={page === 1}
                        className="button"
                    >
                        Précédent
                    </button>
                    <span>
                        Page {page} /{" "}
                        {Math.ceil(sortedHistories.length / HistoriesPerPage)}
                    </span>
                    <button
                        onClick={() =>
                            setPage((p) =>
                                p <
                                Math.ceil(
                                    sortedHistories.length / HistoriesPerPage
                                )
                                    ? p + 1
                                    : p
                            )
                        }
                        disabled={
                            page >=
                            Math.ceil(sortedHistories.length / HistoriesPerPage)
                        }
                    >
                        Suivant
                    </button>
                </div>
            )}
        </div>
    );
}
