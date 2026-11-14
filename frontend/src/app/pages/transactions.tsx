import { useMe } from "../components/hooks/me";
import HistoryTable from "../components/snippets/history_table";
import TransactionsTable from "../components/snippets/transaction_table";

/**
 * Everything the logged-in user may see about trades: the transactions they
 * are part of (and, with the right role, their faction's), and what happened
 * to their offers.
 */
function Transactions() {
    const { user, loading, error } = useMe();

    if (error) return <p role="alert">{error}</p>;
    if (loading || !user) return <p>Chargement...</p>;

    return (
        <div className="information-container">
            <TransactionsTable perPage={15} />
            <HistoryTable
                userId={user.user_id.toString()}
                HistoriesPerPage={15}
            />
        </div>
    );
}

export default Transactions;
