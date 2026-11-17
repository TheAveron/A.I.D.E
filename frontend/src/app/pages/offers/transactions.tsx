import { useMe } from "../../hooks/users/me";
import { useRole } from "../../hooks/factions/role";
import HistoryTable from "../../components/transactions/history_table";
import TransactionsTable from "../../components/transactions/transaction_table";

/**
 * The logged-in user's trades (as buyer or as seller), their faction's trades
 * when their role may see them, and what happened to their offers.
 */
function Transactions() {
    const { user, loading, error } = useMe();
    const { role } = useRole(user?.role_id ?? null);
    // The server only sends a faction's transactions to roles that may see them
    const showFaction =
        !!user?.faction_id &&
        !!role?.view_transactions &&
        role.faction_id === user.faction_id;

    if (error) return <p role="alert">{error}</p>;
    if (loading || !user) return <p>Chargement...</p>;

    return (
        <div className="information-container">
            <TransactionsTable
                userId={user.user_id.toString()}
                perPage={15}
                title="Mes transactions"
            />
            {showFaction && (
                <TransactionsTable
                    factionId={user.faction_id?.toString()}
                    perPage={15}
                    title="Transactions de ma faction"
                />
            )}
            <HistoryTable
                userId={user.user_id.toString()}
                HistoriesPerPage={15}
            />
        </div>
    );
}

export default Transactions;
