import { useParams } from "react-router";
import { useCurrency } from "../../hooks/currencies/factioncurrency";
import { NewCurrency } from "./newcurrency";
import { UpdateCurrencyTotal } from "./updatecurrency";
import { CurrencySettings } from "./currencysettings";
import { CurrencyFactions } from "./currency_factions";
import { FactionCurrencyRequests } from "./currency_requests";
import { useMe } from "../../hooks/users/me";
import { useRole } from "../../hooks/factions/role";
import CurrencyHistoryTable from "./currency_history_table";

export default function CurrencyInfo() {
    const { factionid } = useParams();
    const { currency, loading, error, refresh } = useCurrency(
        factionid ?? null,
    );

    const { user } = useMe();
    const { role } = useRole(user?.role_id ?? null);

    // This faction's own holders of manage_funds: they create a currency,
    // ask for one, answer proposals, or have the faction leave its currency.
    const ownFundsManager =
        !!role?.manage_funds &&
        role.faction_id === user?.faction_id &&
        user?.faction_id?.toString() === factionid;
    // Changing the currency itself: issuer managers and money admins (the
    // server says which, since a faction may use a currency it doesn't issue)
    const canManage = !!currency?.can_manage;
    // The declared total's history: any faction using it, and money admins
    const canSeeHistory = canManage || ownFundsManager;

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
                                {currency.total_in_circulation !==
                                    undefined && (
                                    <div className="info-row">
                                        <span className="info-label">
                                            Quantité en circulation:
                                        </span>
                                        <span className="info-value-field">
                                            {currency.total_in_circulation}
                                        </span>
                                    </div>
                                )}
                                {canManage &&
                                    currency.total_in_circulation !==
                                        undefined && (
                                        <UpdateCurrencyTotal
                                            key={currency.total_in_circulation}
                                            currencyId={currency.currency_id}
                                            currentTotal={
                                                currency.total_in_circulation
                                            }
                                            onUpdated={refresh}
                                        />
                                    )}
                                {canManage && (
                                    <CurrencySettings
                                        key={`${currency.name}/${currency.symbol}`}
                                        currencyId={currency.currency_id}
                                        name={currency.name}
                                        symbol={currency.symbol}
                                        onChanged={refresh}
                                        onDeleted={refresh}
                                    />
                                )}
                                <div className="info-row">
                                    <span className="info-label">
                                        Factions utilisant la monnaie:
                                    </span>
                                </div>
                                <CurrencyFactions
                                    currency={currency}
                                    viewerFactionId={user?.faction_id ?? null}
                                    viewerHoldsFunds={ownFundsManager}
                                    onChanged={refresh}
                                />
                                {ownFundsManager && factionid && (
                                    <FactionCurrencyRequests
                                        factionId={factionid}
                                        hasCurrency
                                        onChanged={refresh}
                                    />
                                )}
                            </div>
                        ) : ownFundsManager && factionid ? (
                            <>
                                <NewCurrency onCreated={refresh} />
                                <FactionCurrencyRequests
                                    factionId={factionid}
                                    hasCurrency={false}
                                    onChanged={refresh}
                                />
                            </>
                        ) : (
                            <p>Pas de monnaie.</p>
                        )
                    ) : (
                        <p>Chargement de la monnaie...</p>
                    )
                ) : (
                    <p>{error}</p>
                )}
            </div>
            {canSeeHistory && currency && (
                <CurrencyHistoryTable
                    key={`${currency.name}/${currency.total_in_circulation}`}
                    currencyId={currency.currency_id}
                />
            )}
        </>
    );
}
