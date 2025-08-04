import { useParams } from "react-router-dom";
import { useCurrency } from "../hooks/factioncurrency";

import "../../../assets/css/components/info.css";
import "../../../assets/css/components/buttons.css";

export default function CurrencyInfo() {
    const { factionid } = useParams();
    const { currency, loading } = useCurrency(factionid ?? null);

    if (!factionid) {
        return <p>No faction id provided</p>;
    }

    if (loading) return <p>Chargement de la monnaie...</p>;

    return (
        <div className="snippet-container faction-page currency-container">
            <div className="info-header">
                <div className="info-title">Monnaie</div>
            </div>
            {currency ? (
                <div className="profile-info">
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
                <div className="button">Créer une monnaie</div>
            )}
        </div>
    );
}
