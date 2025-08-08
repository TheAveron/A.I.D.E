import { useNavigate } from "react-router-dom";
import { useTransactions } from "../hooks/transactions";
import { useOffer } from "../hooks/offers";
import type { TransactionType } from "../../types/transactions";
import { useUser } from "../hooks/user";
import { useFaction } from "../hooks/faction";

export function OfferRow({
    transaction,
    factionId,
    userId,
}: {
    transaction: TransactionType;
    factionId?: string | null;
    userId?: string | null;
}) {
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

    const navigate = useNavigate();

    if (
        faction?.faction_id.toString() != factionId &&
        creatorFaction?.faction_id.toString() != factionId &&
        user?.user_id.toString() != userId &&
        creatorUser?.user_id.toString() != userId &&
        (factionId || userId)
    ) {
        return;
    }

    return (
        <tr key={transaction.offer_id}>
            {!error ? (
                !loading ? (
                    <>
                        <td
                            onClick={() => {
                                navigate(
                                    `/A.I.D.E/user/${transaction.offer_id}`
                                );
                            }}
                            style={{ cursor: "pointer" }}
                        >
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
                                transaction.timestamp
                            ).toLocaleDateString() +
                                ", " +
                                new Date(
                                    transaction.timestamp
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
    const { transactions, loading, error } = useTransactions({
        factionId: null,
        userId: null,
        offerId: offerId,
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
                                            factionId={factionId}
                                            userId={userId}
                                            transaction={transaction}
                                        />
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan={5}>
                                            Aucune Transaction trouvé.
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
