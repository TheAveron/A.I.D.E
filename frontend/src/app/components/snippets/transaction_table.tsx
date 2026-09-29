import { useTransactions } from "../hooks/transactions";
import { useOffer } from "../hooks/offers";
import type { TransactionType } from "../../types/transactions";
import { useUser } from "../hooks/user";
import { useFaction } from "../hooks/faction";

export function OfferRow({ transaction }: { transaction: TransactionType }) {
    const { offer, loading, error } = useOffer(transaction.offer_id);
    const {
        user: creatorUser,
        loading: creatorUserLoading,
        error: creatorUserError,
    } = useUser(offer?.user_id?.toString() ?? null);

    const {
        faction: creatorFaction,
        loading: creatorFactionLoading,
        error: creatorFactionError,
    } = useFaction(offer?.faction_id?.toString() ?? null);

    const {
        user,
        loading: userLoading,
        error: userError,
    } = useUser(transaction.buyer_user_id?.toString() ?? null);

    const {
        faction,
        loading: factionLoading,
        error: factionError,
    } = useFaction(transaction.buyer_faction_id?.toString() ?? null);

    return (
        <tr>
            {!error ? (
                !loading ? (
                    <>
                        <td>
                            {offer ? offer.item_description : "Chargement..."}
                        </td>
                        <td>
                            {!creatorUserLoading || !creatorFactionLoading
                                ? (creatorUserError ??
                                  creatorFactionError ??
                                  creatorUser?.username ??
                                  creatorFaction?.name)
                                : "Chargement..."}
                        </td>
                        <td>
                            {!userLoading || !factionLoading
                                ? (userError ??
                                  factionError ??
                                  user?.username ??
                                  faction?.name)
                                : "Chargement..."}
                        </td>
                        <td>
                            {new Date(
                                transaction.timestamp,
                            ).toLocaleDateString() +
                                ", " +
                                new Date(
                                    transaction.timestamp,
                                ).toLocaleTimeString()}
                        </td>
                    </>
                ) : (
                    <td colSpan={4}>Chargement de la transaction...</td>
                )
            ) : (
                <td colSpan={4}>
                    Erreur lors du chargement de la transaction{" "}
                    {transaction.transaction_id}: {error}
                </td>
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
        </div>
    );
}
