import { useParams } from "react-router-dom";
import { useCurrency } from "../hooks/factioncurrency";

import "../../../assets/css/components/info.css";
import "../../../assets/css/components/buttons.css";
import { NewCurrency } from "../buttons/newcurrency";
import { useAuth } from "../../utils/authprovider";

export default function CurrencyInfo() {
    const { token } = useAuth();

    const { factionid } = useParams();
    const { currency, loading, error } = useCurrency(factionid ?? null);

    return (
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
                        </div>
                    ) : (
                        <NewCurrency />
                    )
                ) : (
                    <p>Chargement de la monnaie...</p>
                )
            ) : (
                <p>{error}</p>
            )}
        </div>
    );
}
