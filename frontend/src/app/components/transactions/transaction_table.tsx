import { useTransactions } from "../../hooks/transactions/transactions";
import type { TransactionType } from "../../types/transactions";
import Username from "../users/username";
import Factionname from "../factions/factionname";
import { Pagination } from "../common/pagination";
import { usePagination } from "../../hooks/common/pagination";

function Actor({
    userId,
    factionId,
}: {
    userId?: number | null;
    factionId?: number | null;
}) {
    if (factionId) return <Factionname factionId={factionId.toString()} />;
    if (userId) return <Username userId={userId.toString()} />;
    return <>-</>;
}

export function OfferRow({ transaction }: { transaction: TransactionType }) {
    return (
        <tr className={transaction.cancelled_at ? "train-retired" : undefined}>
            {/* The server sends what the row shows of the offer */}
            <td>{transaction.offer_item_description ?? "-"}</td>
            <td>
                <Actor
                    userId={transaction.offer_user_id}
                    factionId={transaction.offer_faction_id}
                />
            </td>
            <td>
                <Actor
                    userId={transaction.buyer_user_id}
                    factionId={transaction.buyer_faction_id}
                />
            </td>
            <td>
                {transaction.amount} {transaction.currency_name}
                {transaction.cancelled_at && (
                    <>
                        {" "}
                        <span
                            className="status cancelled"
                            title={transaction.cancel_reason ?? undefined}
                        >
                            Annulée
                        </span>
                    </>
                )}
            </td>
            <td>
                {new Date(transaction.timestamp).toLocaleDateString() +
                    ", " +
                    new Date(transaction.timestamp).toLocaleTimeString()}
            </td>
        </tr>
    );
}

export default function TransactionsTable({
    factionId = null,
    userId = null,
    offerId = null,
    perPage = 10,
    title = "Transactions",
    hideWhenEmpty = false,
}: {
    factionId?: string | null;
    userId?: string | null;
    offerId?: string | null;
    perPage?: number;
    title?: string;
    // On another player's page the server returns only what the viewer took
    // part in, usually nothing: no empty table then
    hideWhenEmpty?: boolean;
}) {
    // The server only returns what the viewer may see and applies the filters.
    const { transactions, loading, error } = useTransactions({
        factionId,
        userId,
        offerId,
    });
    const { pageItems, page, totalPages, setPage } = usePagination(
        transactions ?? [],
        perPage,
    );

    if (hideWhenEmpty && !loading && !error && !transactions?.length) {
        return null;
    }

    return (
        <div className="snippet-container transactions-container">
            <div className="info-header">
                <div className="info-title">{title}</div>
            </div>
            <div className="info-values table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Offre</th>
                            <th>Créateur</th>
                            <th>Acceptant</th>
                            <th>Montant</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {!error ? (
                            !loading ? (
                                pageItems.length > 0 ? (
                                    pageItems.map((transaction) => (
                                        <OfferRow
                                            key={transaction.transaction_id}
                                            transaction={transaction}
                                        />
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan={5}>
                                            Aucune Transaction trouvée.
                                        </td>
                                    </tr>
                                )
                            ) : (
                                <tr>
                                    <td colSpan={5}>
                                        Chargement des transactions...
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
