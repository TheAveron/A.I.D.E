import { useParams } from "react-router";
import { useCurrency } from "../hooks/factioncurrency";
import { NewCurrency } from "../buttons/newcurrency";
import { UpdateCurrencyTotal } from "../buttons/updatecurrency";
import { useMe } from "../hooks/me";
import { useRole } from "../hooks/role";
import CurrencyHistoryTable from "./currency_history_table";

export default function CurrencyInfo() {
    const { factionid } = useParams();
    const { currency, loading, error, refresh } = useCurrency(
        factionid ?? null,
    );

    const { user } = useMe();
    const { role } = useRole(user?.role_id ?? null);

    // The declared total and its audit trail are for this faction's own
    // managers (the server refuses everybody else).
    const canManage =
        !!role?.manage_funds &&
        role.faction_id === user?.faction_id &&
        user?.faction_id?.toString() === factionid;

    return (
        <>
            <div className="snippet-container faction-page currency-container">
                <div className="info-header">
                    <div className="info-title">Monnaie</div>
                </div>
                {!error ? (
                    !loading ? (
                        currency ? (
                            <div className="info-values">
                                <div className="info-row">
                                    <span className="info-label">Nom:</span>
                                    <span className="info-value-field">
                                        {currency.name}
                                    </span>
                                </div>
                                <div className="info-row">
                                    <span className="info-label">Symbole:</span>
                                    <span className="info-value-field">
                                        {currency.symbol ?? "Pas de symbole"}
                                    </span>
                                </div>
                                <div className="info-row">
                                    <span className="info-label">
                                        Quantité en circulation:
                                    </span>
                                    <span className="info-value-field">
                                        {currency.total_in_circulation}
                                    </span>
                                </div>
                                {canManage && (
                                    <UpdateCurrencyTotal
                                        key={currency.total_in_circulation}
                                        currencyName={currency.name}
                                        currentTotal={
                                            currency.total_in_circulation
                                        }
                                        onUpdated={refresh}
                                    />
                                )}
                            </div>
                        ) : (
                            <NewCurrency onCreated={refresh} />
                        )
                    ) : (
                        <p>Chargement de la monnaie...</p>
                    )
                ) : (
                    <p>{error}</p>
                )}
            </div>
            {canManage && currency && (
                <CurrencyHistoryTable
                    key={currency.total_in_circulation}
                    currencyName={currency.name}
                />
            )}
        </>
    );
}
