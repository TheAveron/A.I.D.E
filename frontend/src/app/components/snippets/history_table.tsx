import { useOfferHistoriesByActor } from "../hooks/offer_history";
import Username from "./username";
import Factionname from "./factionname";
import { Offername } from "./offername";
import { useMemo } from "react";
import { Pagination } from "./pagination";
import { usePagination } from "../hooks/pagination";

export default function HistoryTable({
    factionId,
    userId,
    HistoriesPerPage = 10,
}: {
    factionId?: string;
    userId?: string;
    HistoriesPerPage?: number;
}) {
    const { offerHistories, loading, error } = useOfferHistoriesByActor({
        actorFactionId: factionId ?? null,
        actorUserId: userId ?? null,
    });

    const sortedHistories = useMemo(() => {
        const copy = [...(offerHistories || [])];

        copy.sort(
            (a, b) =>
                new Date(b.timestamp).getTime() -
                new Date(a.timestamp).getTime(),
        );

        return copy;
    }, [offerHistories]);

    const {
        pageItems: paginatedHistories,
        page,
        totalPages,
        setPage,
    } = usePagination(sortedHistories, HistoriesPerPage);

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
                                        <tr key={offer.history_id}>
                                            <td>
                                                <Offername
                                                    offerId={offer.offer_id}
                                                />
                                            </td>
                                            <td>
                                                {(
                                                    offer.action ?? ""
                                                ).toLowerCase()}
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
                                                    offer.timestamp,
                                                ).toLocaleDateString() +
                                                    ", " +
                                                    new Date(
                                                        offer.timestamp,
                                                    ).toLocaleTimeString()}
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan={5}>
                                            Aucun historique trouvé.
                                        </td>
                                    </tr>
                                )
                            ) : (
                                <tr>
                                    <td colSpan={5}>
                                        Chargement de l'historique...
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
            <Pagination page={page} totalPages={totalPages} setPage={setPage} />
        </div>
    );
}
