import axios from "axios";
import { useEffect, useState } from "react";
import type { FactionInfo } from "../types/factions";
import { useParams } from "react-router-dom";

function FactionPage() {
    const { factionid } = useParams();
    const [faction, setFaction] = useState<FactionInfo | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<String | null>(null);

    useEffect(() => {
        const fetchFaction = async () => {
            try {
                const res = await axios.get<FactionInfo>(
                    "http://127.0.0.1:8000/factions/" + factionid
                );
                setFaction(res.data);
            } catch (err) {
                setError("Failed to load Faction infos.");
            } finally {
                setLoading(false);
            }
        };

        fetchFaction();
    }, []);

    if (loading) {
        return <p>Loading...</p>;
    }

    if (error) {
        return <p style={{ color: "red" }}>Error: {error}</p>;
    }

    return <>{faction?.name}</>;
}

export default FactionPage;
