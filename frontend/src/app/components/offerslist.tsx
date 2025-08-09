import { useState, useMemo } from "react";

import { NewOffer } from "./buttons/newoffer";
import { useOffersList } from "./hooks/offers";

import type { OfferType } from "../types/offers";
import { AcceptOfferButton } from "./buttons/acceptoffer";
import { useMe } from "./hooks/me";

const STATUS_LABELS: Record<string, string> = {
    OPEN: "Ouvert",
    CLOSED: "Complétée",
    CANCELLED: "Annulée",
};

const STATUS_CLASSES: Record<string, string> = {
    OPEN: "status open",
    CLOSED: "status closed",
    CANCELLED: "status cancelled",
};

function OfferRow({ offer }: { offer: OfferType }) {
    const { user } = useMe();

    return (
        <tr>
            <td>{offer.offer_type === "BUY" ? "Achat" : "Vente"}</td>
            <td>
                <span className={STATUS_CLASSES[offer.status] || "status"}>
                    {STATUS_LABELS[offer.status] || offer.status}
                </span>
            </td>
            <td>{offer.item_description}</td>
            <td>
                {offer.status === "OPEN" ? offer.quantity : offer.init_quantity}
            </td>
            <td>{offer.price_per_unit}</td>
            <td>
                {new Date(offer.created_at).toLocaleDateString("fr-FR", {
                    day: "2-digit",
                    month: "short",
                    year: "numeric",
                })}
            </td>
            <td style={{ maxWidth: "fit-content" }}>
                {offer.status === "OPEN" &&
                (offer.user_id != user?.user_id || user?.faction_id) ? (
                    <AcceptOfferButton
                        offerId={offer.offer_id}
                        offerQuantity={offer.quantity}
                        offerUserId={offer.user_id}
                        offerFactionId={offer.faction_id}
                        onAccepted={() => window.location.reload()}
                    />
                ) : (
                    <></>
                )}
            </td>
        </tr>
    );
}

export default function OfferList({
    userId,
    factionId,
    offersPerPage = 10,
}: {
    userId?: string | null;
    factionId?: string | null;
    offersPerPage?: number;
}) {
    const { offers, loading, error } = useOffersList();
    const [search, setSearch] = useState("");
    const [sortBy, setSortBy] = useState<"price" | "date" | null>(null);
    const [page, setPage] = useState(1);

    const normalizedUserId = userId?.toString();
    const normalizedFactionId = factionId?.toString();

    const filteredOffers = useMemo(() => {
        return (
            offers?.filter((offer) => {
                const matchUser =
                    normalizedUserId == null ||
                    offer.user_id?.toString() === normalizedUserId;
                const matchFaction =
                    normalizedFactionId == null ||
                    offer.faction_id?.toString() === normalizedFactionId;
                const matchSearch = offer.item_description
                    .toLowerCase()
                    .includes(search.toLowerCase());

                return matchUser && matchFaction && matchSearch;
            }) || []
        );
    }, [offers, normalizedUserId, normalizedFactionId, search]);

    const sortedOffers = useMemo(() => {
        const copy = [...filteredOffers];

        if (sortBy === "price") {
            copy.sort((a, b) => a.price_per_unit - b.price_per_unit);
        } else if (sortBy === "date") {
            copy.sort(
                (a, b) =>
                    new Date(b.created_at).getTime() -
                    new Date(a.created_at).getTime()
            );
        }
        return copy;
    }, [filteredOffers, sortBy]);

    const paginatedOffers = useMemo(() => {
        const start = (page - 1) * offersPerPage;
        return sortedOffers.slice(start, start + offersPerPage);
    }, [sortedOffers, page]);

    return (
        <div className="snippet-container offers-container">
            <div className="offers-header">
                <h2>Liste des offres</h2>
                <NewOffer />
            </div>

            <div className="toolbar">
                <input
                    type="text"
                    placeholder="Rechercher un item..."
                    value={search}
                    onChange={(e) => {
                        setSearch(e.target.value);
                        setPage(1);
                    }}
                />
                <div className="sort-controls">
                    <div className="button" onClick={() => setSortBy("price")}>
                        Trier par prix
                    </div>
                    <div className="button" onClick={() => setSortBy("date")}>
                        Trier par date
                    </div>
                </div>
            </div>

            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Type</th>
                            <th>Statut</th>
                            <th>Item</th>
                            <th>Quantité</th>
                            <th>Prix par unité</th>
                            <th>Création</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {error ? (
                            <tr>
                                <td colSpan={7} style={{ color: "red" }}>
                                    Erreur lors du chargement des offres.
                                </td>
                            </tr>
                        ) : loading ? (
                            <tr>
                                <td colSpan={7}>Chargement des offres...</td>
                            </tr>
                        ) : paginatedOffers.length > 0 ? (
                            paginatedOffers.map((offer) => (
                                <OfferRow key={offer.offer_id} offer={offer} />
                            ))
                        ) : (
                            <tr className="empty-state">
                                <td colSpan={7}>Aucune offre disponible.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {sortedOffers.length > offersPerPage && (
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
                        {Math.ceil(sortedOffers.length / offersPerPage)}
                    </span>
                    <button
                        onClick={() =>
                            setPage((p) =>
                                p <
                                Math.ceil(sortedOffers.length / offersPerPage)
                                    ? p + 1
                                    : p
                            )
                        }
                        disabled={
                            page >=
                            Math.ceil(sortedOffers.length / offersPerPage)
                        }
                    >
                        Suivant
                    </button>
                </div>
            )}
        </div>
    );
}
