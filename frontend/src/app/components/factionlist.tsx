import { Link } from "react-router-dom";
import { NewFaction } from "./buttons/newfaction";
import { useFactions } from "./hooks/factions";
import { useCurrency } from "./hooks/factioncurrency";

import { useMe } from "./hooks/me";
import MemberCounter from "./snippets/member_count";

import "../../assets/css/components/tables.css";
import "../../assets/css/components/snippets.css";
import "../../assets/css/components/factions.css";

function CurrencyCell({ factionId }: { factionId: string }) {
    const { currency, loading, error } = useCurrency(factionId);

    return (
        <div className="faction-meta">
            {!error ? (
                !loading ? (
                    currency ? (
                        <>{currency.name || "Unknown"}</>
                    ) : (
                        "Pas de monnaie"
                    )
                ) : (
                    <p>Chargement...</p>
                )
            ) : (
                <p>{error}</p>
            )}
        </div>
    );
}

function FactionList() {
    const { factions, loading, error } = useFactions();
    const { user } = useMe();

    return (
        <div className="snippet-container factions-container">
            <div className="factions-header">
                <h2>Liste des factions</h2>
                {!user?.faction_id ? <NewFaction /> : <></>}
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
                    {!error ? (
                        !loading ? (
                            factions && factions.length > 0 ? (
                                factions.map((faction) => (
                                    <Link
                                        key={faction.faction_id}
                                        to={
                                            "/A.I.D.E/faction/" +
                                            faction.faction_id
                                        }
                                        style={{ display: "table-row" }}
                                    >
                                        <td>{faction.name}</td>
                                        <td className="faction-description">
                                            {faction.description?.trim()
                                                ? faction.description
                                                : "No description provided."}
                                        </td>
                                        <td>
                                            <MemberCounter
                                                faction_id={faction.faction_id.toString()}
                                            />
                                        </td>
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
                            )
                        ) : (
                            <tr>
                                <td colSpan={5}>Chargement des faction...</td>
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
    );
}

export default FactionList;
