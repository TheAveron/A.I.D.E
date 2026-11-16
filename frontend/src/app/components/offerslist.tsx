import { useEffect, useState, useMemo } from "react";

import { NewOffer } from "./buttons/newoffer";
import { useOffersList } from "./hooks/offers";

import type { OfferType } from "../types/offers";
import type { UserType } from "../types/users";
import { AcceptOfferButton } from "./buttons/acceptoffer";
import { useMe } from "./hooks/me";
import { useRole } from "./hooks/role";
import { ManageOfferButtons } from "./buttons/manageoffer";
import ToolbarPanels from "./snippets/toolbar_panels";
import { formatExpiry } from "../utils/expiry";

import SortControl from "./snippets/sort_control";
import { sortSummary, type SortOption } from "./snippets/sort_utils";

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

const SERVER_OFFER_LIMIT = 200;

function OfferRow({
    offer,
    user,
    canManage,
    onAccepted,
    onChanged,
}: {
    offer: OfferType;
    user: UserType | null;
    // Whether the viewer may change or cancel this offer
    canManage: boolean;
    onAccepted: () => void;
    onChanged: () => void;
}) {
    return (
        <tr>
            <td>{offer.offer_type === "BUY" ? "Achat" : "Vente"}</td>
            <td>
                <span className={STATUS_CLASSES[offer.status] || "status"}>
                    {STATUS_LABELS[offer.status] || offer.status}
                </span>
                {offer.status === "OPEN" && offer.expires_at && (
                    <small> jusqu'au {formatExpiry(offer.expires_at)}</small>
                )}
            </td>
            <td>
                {offer.item_description}
                {offer.is_private && (
                    <span
                        className="status"
                        title="Visible seulement par les destinataires"
                    >
                        {" "}
                        🔒 Privée
                    </span>
                )}
            </td>
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
                {offer.status === "OPEN" && canManage && (
                    <ManageOfferButtons
                        key={`${offer.price_per_unit}/${offer.quantity}`}
                        offer={offer}
                        onChanged={onChanged}
                    />
                )}
            </td>
        </tr>
    );
}

const SORT_OPTIONS: SortOption<"price" | "date">[] = [
    { value: "date", label: "Date" },
    { value: "price", label: "Prix" },
];

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
    // The text is sent to the server once typing pauses
    const [searchSent, setSearchSent] = useState("");
    const [typeFilter, setTypeFilter] = useState("");
    const [minPrice, setMinPrice] = useState("");
    const [maxPrice, setMaxPrice] = useState("");
    const [statusFilter, setStatusFilter] = useState("");
    const [currencyFilter, setCurrencyFilter] = useState("");
    const [knownCurrencies, setKnownCurrencies] = useState<string[]>([]);
    const [sortBy, setSortBy] = useState<"price" | "date" | null>(null);
    const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
    const [page, setPage] = useState(1);

    const { user } = useMe();
    const { role } = useRole(user?.role_id ?? null);
    // Same rule as the API: one's own offers, or one's faction's with create_offers
    const canManageOffer = (offer: OfferType) =>
        !!user &&
        (offer.user_id === user.user_id ||
            (offer.faction_id != null &&
                offer.faction_id === user.faction_id &&
                !!role?.create_offers &&
                role.faction_id === user.faction_id));

    useEffect(() => {
        const timer = setTimeout(() => setSearchSent(search), 300);
        return () => clearTimeout(timer);
    }, [search]);

    const { offers, loading, error, refresh } = useOffersList({
        currency: currencyFilter || undefined,
        status: statusFilter || undefined,
        offerType: typeFilter || undefined,
        search: searchSent,
        minPrice,
        maxPrice,
        userId,
        factionId,
    });

    useEffect(() => {
        setKnownCurrencies((current) => {
            const currencies = new Set(current);
            offers?.forEach((offer) => currencies.add(offer.currency_name));
            return [...currencies].sort((a, b) => a.localeCompare(b));
        });
    }, [offers]);

    const sortedOffers = useMemo(() => {
        const copy = [...(offers ?? [])];

        if (sortBy === "price") {
            copy.sort((a, b) => a.price_per_unit - b.price_per_unit);
        } else if (sortBy === "date") {
            copy.sort(
                (a, b) =>
                    new Date(a.created_at).getTime() -
                    new Date(b.created_at).getTime(),
            );
        }
        return sortDirection === "asc" ? copy : copy.reverse();
    }, [offers, sortBy, sortDirection]);

    const totalPages = Math.ceil(sortedOffers.length / offersPerPage);

    const currentPage = Math.min(page, Math.max(totalPages, 1));

    const paginatedOffers = useMemo(() => {
        const start = (currentPage - 1) * offersPerPage;
        return sortedOffers.slice(start, start + offersPerPage);
    }, [sortedOffers, currentPage, offersPerPage]);

    return (
        <div className="snippet-container offers-container">
            <div className="offers-header">
                <h2>Liste des offres</h2>
                <NewOffer onCreated={refresh} />
            </div>

            <ToolbarPanels
                activeFilters={
                    [
                        typeFilter,
                        minPrice,
                        maxPrice,
                        statusFilter,
                        currencyFilter,
                    ].filter(Boolean).length
                }
                sortSummary={sortSummary(SORT_OPTIONS, sortBy, sortDirection)}
                search={
                    <input
                        type="text"
                        placeholder="Rechercher un item..."
                        value={search}
                        onChange={(e) => {
                            setSearch(e.target.value);
                            setPage(1);
                        }}
                    />
                }
                filters={
                    <>
                        <select
                            aria-label="Filtrer par type"
                            value={typeFilter}
                            onChange={(event) => {
                                setTypeFilter(event.target.value);
                                setPage(1);
                            }}
                        >
                            <option value="">Achats et ventes</option>
                            <option value="SELL">Ventes</option>
                            <option value="BUY">Achats</option>
                        </select>
                        <input
                            type="number"
                            min="0"
                            step="any"
                            aria-label="Prix minimum"
                            placeholder="Prix min"
                            value={minPrice}
                            onChange={(e) => {
                                setMinPrice(e.target.value);
                                setPage(1);
                            }}
                        />
                        <input
                            type="number"
                            min="0"
                            step="any"
                            aria-label="Prix maximum"
                            placeholder="Prix max"
                            value={maxPrice}
                            onChange={(e) => {
                                setMaxPrice(e.target.value);
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
                    </>
                }
                sort={
                    <SortControl
                        options={SORT_OPTIONS}
                        value={sortBy}
                        direction={sortDirection}
                        noneLabel="Par défaut"
                        defaultDirection={(value) =>
                            value === "date" ? "desc" : "asc"
                        }
                        onChange={(value, direction) => {
                            setSortBy(value);
                            setSortDirection(direction);
                            setPage(1);
                        }}
                    />
                }
            />

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
                                    user={user}
                                    canManage={canManageOffer(offer)}
                                    onAccepted={refresh}
                                    onChanged={refresh}
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

            {(offers?.length ?? 0) >= SERVER_OFFER_LIMIT && (
                <p className="empty-state">
                    Seules les {SERVER_OFFER_LIMIT} offres les plus récentes
                    sont affichées : affinez avec les filtres.
                </p>
            )}

            {totalPages > 1 && (
                <div className="pagination-controls">
                    <button
                        onClick={() => setPage(Math.max(currentPage - 1, 1))}
                        disabled={currentPage === 1}
                        className="button"
                    >
                        Précédent
                    </button>
                    <span>
                        Page {currentPage} / {totalPages}
                    </span>
                    <button
                        onClick={() =>
                            setPage(Math.min(currentPage + 1, totalPages))
                        }
                        disabled={currentPage >= totalPages}
                        className="button"
                    >
                        Suivant
                    </button>
                </div>
            )}
        </div>
    );
}
