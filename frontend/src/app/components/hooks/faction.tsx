import { useEffect, useState } from "react";
import axios from "axios";
import { useAuth } from "../../utils/authprovider";
import { type FactionType } from "../../types/factions";

export function useFaction(faction_id: string | null) {
    const { token } = useAuth();
    const [faction, setFaction] = useState<FactionType | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!token || !faction_id) return;

        const fetchFaction = async () => {
            try {
                setLoading(true);
                const res = await axios.get<FactionType>(
                    `http://127.0.0.1:8000/factions/detail/${faction_id}`
                );
                setFaction(res.data);
            } catch (error) {
                console.error("Error fetching faction:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchFaction();
    }, [token, faction_id]);

    return { faction, loading };
}
