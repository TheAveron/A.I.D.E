import axios from "axios";
import { useState } from "react";

import AdminPager from "./admin_pager";
import ToolbarPanels from "./toolbar_panels";
import { useAdminTransactions } from "../hooks/admin";
import { getErrorMessage } from "../../utils/apierror";
import { askReason } from "../../utils/audit";
import type {
    AdminTransactionCancelled,
    AdminTransactionType,
    TransactionState,
} from "../../types/admin";

const STATES: [TransactionState, string][] = [
    ["all", "Toutes"],
    ["active", "En vigueur"],
    ["cancelled", "Annulées"],
];

/** Every transaction; an admin can cancel one, which gives its units back. */
export default function AdminTransactions() {
    const [state, setState] = useState<TransactionState>("all");
    const [search, setSearch] = useState("");
    const [page, setPage] = useState(1);
    const [message, setMessage] = useState("");
    const { transactions, loading, error, refresh } = useAdminTransactions(
        state,
        search,
        page,
    );

    const cancel = async (t: AdminTransactionType) => {
        const reason = askReason(
            `Annuler la transaction n°${t.transaction_id} (« ${t.item_description} », ${t.amount} ${t.currency_name}) ?`,
        );
        if (!reason) return;
        setMessage("");
        try {
            const res = await axios.post<AdminTransactionCancelled>(
                `/admin/transactions/${t.transaction_id}/cancel`,
                { reason },
            );
            const { quantity_restored, offer_reopened } = res.data;
            setMessage(
                `✅ Transaction n°${t.transaction_id} annulée. ` +
                    (quantity_restored
                        ? offer_reopened
                            ? "Les unités sont revenues sur l'offre, qui est rouverte."
                            : "Les unités sont revenues sur l'offre."
                        : "Aucune unité remise sur l'offre (ancienne transaction ou offre annulée)."),
            );
            refresh();
        } catch (err) {
            setMessage(`❌ ${getErrorMessage(err)}`);
        }
    };

    return (
        <div className="snippet-container">
            <h2>Transactions</h2>
            <ToolbarPanels
                activeFilters={state !== "all" ? 1 : 0}
                search={
                    <input
                        type="text"
                        placeholder="Rechercher un objet..."
                        aria-label="Rechercher une transaction"
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
                            setState(e.target.value as TransactionState);
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
                            <th>N°</th>
                            <th>Offre</th>
                            <th>Vendeur</th>
                            <th>Acheteur</th>
                            <th>Montant</th>
                            <th>Date</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {error ? (
                            <tr>
                                <td colSpan={7}>{error}</td>
                            </tr>
                        ) : loading ? (
                            <tr>
                                <td colSpan={7}>Chargement...</td>
                            </tr>
                        ) : transactions.length === 0 ? (
                            <tr className="empty-state">
                                <td colSpan={7}>Aucune transaction.</td>
                            </tr>
                        ) : (
                            transactions.map((t) => (
                                <tr
                                    key={t.transaction_id}
                                    className={
                                        t.cancelled_at
                                            ? "train-retired"
                                            : undefined
                                    }
                                >
                                    <td>{t.transaction_id}</td>
                                    <td>
                                        {t.item_description}
                                        {t.quantity !== null && (
                                            <small> ×{t.quantity}</small>
                                        )}
                                    </td>
                                    <td>{t.seller_name ?? "-"}</td>
                                    <td>{t.buyer_name ?? "-"}</td>
                                    <td>
                                        {t.amount} {t.currency_name}
                                    </td>
                                    <td>
                                        {new Date(t.timestamp).toLocaleString(
                                            "fr-FR",
                                        )}
                                    </td>
                                    <td>
                                        {t.cancelled_at ? (
                                            <span
                                                className="status cancelled"
                                                title={`Par ${t.cancelled_by_name ?? "?"} : ${t.cancel_reason ?? ""}`}
                                            >
                                                Annulée
                                            </span>
                                        ) : (
                                            <button
                                                type="button"
                                                className="button"
                                                onClick={() => cancel(t)}
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
            <AdminPager
                page={page}
                count={transactions.length}
                setPage={setPage}
            />
        </div>
    );
}
