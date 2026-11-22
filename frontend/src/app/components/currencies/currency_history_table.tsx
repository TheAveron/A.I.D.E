import { useCurrencyHistory } from "../../hooks/currencies/currency_history";
import { usePagination } from "../../hooks/common/pagination";
import { Pagination } from "../common/pagination";
import Username from "../users/username";

const COLUMNS = 5;

export default function CurrencyHistoryTable({
    currencyId,
    perPage = 10,
}: {
    currencyId: number;
    perPage?: number;
}) {
    const { histories, loading, error } = useCurrencyHistory(currencyId);
    const { pageItems, page, totalPages, setPage } = usePagination(
        histories ?? [],
        perPage,
    );

    return (
        <div className="snippet-container history-container">
            <h2>Historique de la monnaie</h2>
            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Par</th>
                            <th>Avant</th>
                            <th>Après</th>
                            <th>Motif</th>
                        </tr>
                    </thead>
                    <tbody>
                        {error ? (
                            <tr>
                                <td colSpan={COLUMNS}>{error}</td>
                            </tr>
                        ) : loading ? (
                            <tr>
                                <td colSpan={COLUMNS}>
                                    Chargement de l'historique...
                                </td>
                            </tr>
                        ) : pageItems.length === 0 ? (
                            <tr>
                                <td colSpan={COLUMNS}>
                                    Aucune modification enregistrée.
                                </td>
                            </tr>
                        ) : (
                            pageItems.map((entry) => (
                                <tr key={entry.history_id}>
                                    <td>
                                        {new Date(
                                            entry.timestamp,
                                        ).toLocaleDateString() +
                                            ", " +
                                            new Date(
                                                entry.timestamp,
                                            ).toLocaleTimeString()}
                                    </td>
                                    <td>
                                        {entry.actor_user_id ? (
                                            <Username
                                                userId={entry.actor_user_id.toString()}
                                            />
                                        ) : (
                                            "-"
                                        )}
                                    </td>
                                    <td>{entry.old_total_in_circulation}</td>
                                    <td>{entry.new_total_in_circulation}</td>
                                    <td>{entry.notes ?? ""}</td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
            <Pagination page={page} totalPages={totalPages} setPage={setPage} />
        </div>
    );
}
