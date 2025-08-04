import { Link } from "react-router-dom";
import { NewFaction } from "./buttons/newfaction";
import { useFactions } from "./hooks/factions";
import { useCurrency } from "./hooks/factioncurrency";

import "../../assets/css/components/tables.css";
import "../../assets/css/components/snippets.css";
import "../../assets/css/components/factions.css";

function CurrencyCell({ factionId }: { factionId: string }) {
    const { currency } = useCurrency(factionId);

    return (
        <div className="faction-meta">
            {currency ? (
                <>
                    <span className="currency">
                        {currency.name || "Unknown"}
                    </span>
                    <span className="amount">
                        {currency.total_in_circulation || 0}
                    </span>
                </>
            ) : (
                "Pas de monnaie"
            )}
        </div>
    );
}

function FactionList() {
    const { factions, loading } = useFactions();

    if (loading) {
        return <p>Loading...</p>;
    }

    return (
        <div className="snippet-container factions-container">
            <div className="factions-header">
                <h2>Liste des factions</h2>
                <NewFaction />
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Nom</th>
                        <th>Description</th>
                        <th>Nombre de membres</th>
                        <th>Monnaie</th>
                        <th>Validation</th>
                    </tr>
                </thead>
                <tbody>
                    {factions && factions.length > 0 ? (
                        factions.map((faction) => (
                            <Link
                                key={faction.faction_id}
                                to={"/A.I.D.E/faction/" + faction.faction_id}
                                style={{ display: "table-row" }}
                            >
                                <td>{faction.name}</td>
                                <td className="faction-description">
                                    {faction.description?.trim()
                                        ? faction.description
                                        : "No description provided."}
                                </td>
                                <td>{/* TODO: Add member count */}</td>
                                <td>
                                    <CurrencyCell
                                        factionId={faction.faction_id.toString()}
                                    />
                                </td>
                                <td>
                                    <div
                                        className={`status ${
                                            faction.is_approved
                                                ? "approved"
                                                : "not-approved"
                                        }`}
                                    >
                                        {faction.is_approved
                                            ? "Validée ✅"
                                            : "En attente ⏳"}
                                    </div>
                                </td>
                            </Link>
                        ))
                    ) : (
                        <tr>
                            <td colSpan={5}>Aucune faction trouvée.</td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
}

export default FactionList;
