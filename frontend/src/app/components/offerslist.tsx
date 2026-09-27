import { useEffect, useState, useMemo } from "react";

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

function OfferRow({
    offer,
    onAccepted,
}: {
    offer: OfferType;
    onAccepted: () => void;
}) {
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
                offer.user_id !== user?.user_id &&
                (offer.faction_id == null ||
                    offer.faction_id !== user?.faction_id) ? (
                    <AcceptOfferButton
                        offerId={offer.offer_id}
                        offerQuantity={offer.quantity}
                        offerUserId={offer.user_id}
                        offerFactionId={offer.faction_id}
                        onAccepted={onAccepted}
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
    const [search, setSearch] = useState("");
    const [statusFilter, setStatusFilter] = useState("");
    const [currencyFilter, setCurrencyFilter] = useState("");
    const [knownCurrencies, setKnownCurrencies] = useState<string[]>([]);
    const [sortBy, setSortBy] = useState<"price" | "date" | null>(null);
    const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
    const [page, setPage] = useState(1);

    const { offers, loading, error, refresh } = useOffersList(
        currencyFilter || undefined,
        statusFilter || undefined,
    );

    useEffect(() => {
        setKnownCurrencies((current) => {
            const currencies = new Set(current);
            offers?.forEach((offer) => currencies.add(offer.currency_name));
            return [...currencies].sort((a, b) => a.localeCompare(b));
        });
    }, [offers]);

    const normalizedUserId = userId?.toString();
    const normalizedFactionId = factionId?.toString();

    const filteredOffers = useMemo(() => {
        const term = (search ?? "").toLowerCase();
        return (
            offers?.filter((offer) => {
                const matchUser =
                    normalizedUserId == null ||
                    offer.user_id?.toString() === normalizedUserId;

                const matchFaction =
                    normalizedFactionId == null ||
                    offer.faction_id?.toString() === normalizedFactionId;

                const matchSearch = (offer.item_description ?? "")
                    .toLowerCase()
                    .includes(term);

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
                    new Date(a.created_at).getTime(),
            );
        }
        return sortDirection === "asc" ? copy : copy.reverse();
    }, [filteredOffers, sortBy, sortDirection]);

    const selectSort = (nextSort: "price" | "date") => {
        if (sortBy === nextSort) {
            setSortDirection((direction) =>
                direction === "asc" ? "desc" : "asc",
            );
        } else {
            setSortBy(nextSort);
            setSortDirection("asc");
        }
        setPage(1);
    };

    const totalPages = Math.ceil(sortedOffers.length / offersPerPage);

    useEffect(() => {
        setPage((currentPage) =>
            Math.min(Math.max(currentPage, 1), totalPages || 1),
        );
    }, [totalPages]);

    const paginatedOffers = useMemo(() => {
        const start = (page - 1) * offersPerPage;
        return sortedOffers.slice(start, start + offersPerPage);
    }, [sortedOffers, page, offersPerPage]);

    return (
        <div className="snippet-container offers-container">
            <div className="offers-header">
                <h2>Liste des offres</h2>
                <NewOffer onCreated={refresh} />
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
                <select
                    aria-label="Filtrer par statut"
                    value={statusFilter}
                    onChange={(event) => {
                        setStatusFilter(event.target.value);
                        setPage(1);
                    }}
                >
                    <option value="">Tous les statuts</option>
                    <option value="OPEN">Ouvertes</option>
                    <option value="CLOSED">Complétées</option>
                    <option value="CANCELLED">Annulées</option>
                </select>
                <select
                    aria-label="Filtrer par monnaie"
                    value={currencyFilter}
                    onChange={(event) => {
                        setCurrencyFilter(event.target.value);
                        setPage(1);
                    }}
                >
                    <option value="">Toutes les monnaies</option>
                    {knownCurrencies.map((currency) => (
                        <option key={currency} value={currency}>
                            {currency}
                        </option>
                    ))}
                </select>
                <div className="sort-controls">
                    <button
                        type="button"
                        className="button"
                        aria-pressed={sortBy === "price"}
                        onClick={() => selectSort("price")}
                    >
                        Prix{" "}
                        {sortBy === "price" &&
                            (sortDirection === "asc" ? "↑" : "↓")}
                    </button>
                    <button
                        type="button"
                        className="button"
                        aria-pressed={sortBy === "date"}
                        onClick={() => selectSort("date")}
                    >
                        Date{" "}
                        {sortBy === "date" &&
                            (sortDirection === "asc" ? "↑" : "↓")}
                    </button>
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
                                    <button
                                        type="button"
                                        className="button"
                                        onClick={refresh}
                                    >
                                        Réessayer
                                    </button>
                                </td>
                            </tr>
                        ) : loading ? (
                            <tr>
                                <td colSpan={7}>Chargement des offres...</td>
                            </tr>
                        ) : paginatedOffers.length > 0 ? (
                            paginatedOffers.map((offer) => (
                                <OfferRow
                                    key={offer.offer_id}
                                    offer={offer}
                                    onAccepted={refresh}
                                />
                            ))
                        ) : (
                            <tr className="empty-state">
                                <td colSpan={7}>Aucune offre disponible.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {totalPages > 1 && (
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
                            setPage((p) => (p < totalPages ? p + 1 : p))
                        }
                        disabled={page >= totalPages}
                    >
                        Suivant
                    </button>
                </div>
            )}
        </div>
    );
}
