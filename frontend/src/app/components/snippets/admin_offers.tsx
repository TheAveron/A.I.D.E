import axios from "axios";
import { useState } from "react";
import { Link } from "react-router";

import AdminPager from "./admin_pager";
import ToolbarPanels from "./toolbar_panels";
import { useAdminOffers } from "../hooks/admin";
import { getErrorMessage } from "../../utils/apierror";
import { askReason } from "../../utils/audit";
import { formatExpiry } from "../../utils/expiry";
import type { AdminOfferType, OfferState } from "../../types/admin";

const STATES: [OfferState, string][] = [
    ["all", "Toutes"],
    ["open", "Ouvertes"],
    ["closed", "Complétées"],
    ["cancelled", "Annulées"],
];

const STATUS_LABELS: Record<string, string> = {
    OPEN: "Ouverte",
    CLOSED: "Complétée",
    CANCELLED: "Annulée",
};

/** Every offer, private ones included; an admin can cancel any open one. */
export default function AdminOffers() {
    const [state, setState] = useState<OfferState>("open");
    const [search, setSearch] = useState("");
    const [page, setPage] = useState(1);
    const [message, setMessage] = useState("");
    const { offers, loading, error, refresh } = useAdminOffers(
        state,
        search,
        page,
    );

    const cancel = async (offer: AdminOfferType) => {
        const reason = askReason(
            `Annuler l'offre « ${offer.item_description} » de ${offer.owner_name ?? "?"} ?`,
        );
        if (!reason) return;
        setMessage("");
        try {
            await axios.post(`/admin/offers/${offer.offer_id}/cancel`, {
                reason,
            });
            setMessage(`✅ Offre « ${offer.item_description} » annulée`);
            refresh();
        } catch (err) {
            setMessage(`❌ ${getErrorMessage(err)}`);
        }
    };

    return (
        <div className="snippet-container">
            <h2>Offres</h2>
            <ToolbarPanels
                activeFilters={state !== "open" ? 1 : 0}
                search={
                    <input
                        type="text"
                        placeholder="Rechercher un objet..."
                        aria-label="Rechercher une offre"
                        maxLength={100}
                        value={search}
                        onChange={(e) => {
                            setSearch(e.target.value);
                            setPage(1);
                        }}
                    />
                }
                filters={
                    <select
                        aria-label="Filtrer par état"
                        value={state}
                        onChange={(e) => {
                            setState(e.target.value as OfferState);
                            setPage(1);
                        }}
                    >
                        {STATES.map(([value, label]) => (
                            <option key={value} value={value}>
                                {label}
                            </option>
                        ))}
                    </select>
                }
            />
            {message && <p role="status">{message}</p>}
            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Offre</th>
                            <th>Propriétaire</th>
                            <th>Quantité</th>
                            <th>Prix</th>
                            <th>État</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {error ? (
                            <tr>
                                <td colSpan={6}>{error}</td>
                            </tr>
                        ) : loading ? (
                            <tr>
                                <td colSpan={6}>Chargement...</td>
                            </tr>
                        ) : offers.length === 0 ? (
                            <tr className="empty-state">
                                <td colSpan={6}>Aucune offre.</td>
                            </tr>
                        ) : (
                            offers.map((o) => (
                                <tr key={o.offer_id}>
                                    <td>
                                        {o.offer_type === "BUY"
                                            ? "Achat"
                                            : "Vente"}{" "}
                                        {o.item_description}
                                        {o.is_private && (
                                            <>
                                                {" "}
                                                <span className="status">
                                                    🔒 Privée
                                                </span>
                                            </>
                                        )}
                                    </td>
                                    <td>
                                        {o.owner_id !== null ? (
                                            <Link
                                                to={
                                                    o.owner_kind === "user"
                                                        ? `/user/${o.owner_id}`
                                                        : `/faction/${o.owner_id}`
                                                }
                                            >
                                                {o.owner_name ??
                                                    `#${o.owner_id}`}
                                            </Link>
                                        ) : (
                                            "-"
                                        )}
                                    </td>
                                    <td>
                                        {o.status === "OPEN"
                                            ? o.quantity
                                            : o.init_quantity}
                                    </td>
                                    <td>
                                        {o.price_per_unit} {o.currency_name}
                                    </td>
                                    <td>
                                        {STATUS_LABELS[o.status] ?? o.status}
                                        {o.status === "OPEN" &&
                                            o.expires_at && (
                                                <small>
                                                    {" "}
                                                    jusqu&apos;au{" "}
                                                    {formatExpiry(o.expires_at)}
                                                </small>
                                            )}
                                    </td>
                                    <td>
                                        {o.status === "OPEN" && (
                                            <button
                                                type="button"
                                                className="button"
                                                onClick={() => cancel(o)}
                                            >
                                                Annuler
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
            <AdminPager page={page} count={offers.length} setPage={setPage} />
        </div>
    );
}
