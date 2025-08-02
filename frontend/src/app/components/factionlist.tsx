import { useEffect, useState } from "react";
import type { FactionInfo } from "../types/factions";
import axios from "axios";
import "../../assets/css/components/factions.css";
import { Link } from "react-router-dom";

function FactionList() {
    const [factions, setFactions] = useState<FactionInfo[] | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<String | null>(null);

    useEffect(() => {
        const fetchFactions = async () => {
            try {
                const res = await axios.get<FactionInfo[]>(
                    "http://127.0.0.1:8000/factions/list"
                );
                setFactions(res.data);
            } catch (err) {
                setError("Failed to load Faction infos.");
            } finally {
                setLoading(false);
            }
        };

        fetchFactions();
    }, []);

    if (loading) {
        return <p>Loading...</p>;
    }

    if (error) {
        return <p style={{ color: "red" }}>Error: {error}</p>;
    }

    if (!factions || factions.length === 0) {
        return <p>No factions found.</p>;
    }

    return (
        <div className="snippet-container">
            <div className="factions-header">
                <h2>Liste des factions</h2>
            </div>
            <div className="factions-infos">
                <div className="row list-head">
                    <div className="row-element">Name</div>
                    <div className="row-element">Descritpion</div>
                    <div className="row-element">Currency</div>
                    <div className="row-element">Status</div>
                </div>
            </div>
            <div className="list">
                {factions.map((faction) => (
                    <Link
                        className="row"
                        key={faction.faction_id}
                        to={"/A.I.D.E/faction/" + faction.faction_id}
                    >
                        <div className="row-element">
                            <h2 className="faction-name">{faction.name}</h2>
                        </div>
                        <div className="row-element">
                            <p className="faction-description">
                                {faction.description?.trim()
                                    ? faction.description
                                    : "No description provided."}
                            </p>
                        </div>

                        <div className="row-element">
                            <div className="faction-meta">
                                <span className="currency">
                                    {faction.currency_name || "Unknown"}
                                </span>
                                <span className="amount">
                                    {faction.currency_amount}
                                </span>
                            </div>
                        </div>
                        <div className="row-element">
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
                        </div>
                    </Link>
                ))}
            </div>
        </div>
    );
}

export default FactionList;
