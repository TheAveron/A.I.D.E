import { useTransactions } from "../hooks/transactions";
import { useOffer } from "../hooks/offers";
import type { TransactionType } from "../../types/transactions";
import Username from "./username";
import Factionname from "./factionname";

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
    const { offer, loading, error } = useOffer(transaction.offer_id);

    return (
        <tr>
            {error ? (
                <td colSpan={4}>
                    Erreur lors du chargement de la transaction{" "}
                    {transaction.transaction_id}: {error}
                </td>
            ) : loading || !offer ? (
                <td colSpan={4}>Chargement de la transaction...</td>
            ) : (
                <>
                    <td>{offer.item_description}</td>
                    <td>
                        <Actor
                            userId={offer.user_id}
                            factionId={offer.faction_id}
                        />
                    </td>
                    <td>
                        <Actor
                            userId={transaction.buyer_user_id}
                            factionId={transaction.buyer_faction_id}
                        />
                    </td>
                    <td>
                        {new Date(transaction.timestamp).toLocaleDateString() +
                            ", " +
                            new Date(
                                transaction.timestamp,
                            ).toLocaleTimeString()}
                    </td>
                </>
            )}
        </tr>
    );
}

export default function TransactionsTable({
    factionId = null,
    userId = null,
    offerId = null,
}: {
    factionId?: string | null;
    userId?: string | null;
    offerId?: string | null;
}) {
    // The server only returns what the viewer may see and applies the filters.
    const { transactions, loading, error } = useTransactions({
        factionId,
        userId,
        offerId,
    });
    return (
        <div className="snippet-container transactions-container">
            <div className="info-header">
                <div className="info-title">Transactions</div>
            </div>
            <div className="info-values table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Offre</th>
                            <th>Créateur</th>
                            <th>Acceptant</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {!error ? (
                            !loading ? (
                                transactions && transactions.length > 0 ? (
                                    transactions.map((transaction) => (
                                        <OfferRow
                                            key={transaction.transaction_id}
                                            transaction={transaction}
                                        />
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan={4}>
                                            Aucune Transaction trouvée.
                                        </td>
                                    </tr>
                                )
                            ) : (
                                <tr>
                                    <td colSpan={4}>
                                        Chargement des transactions...
                                    </td>
                                </tr>
                            )
                        ) : (
                            <tr>
                                <td colSpan={4}>{error}</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
