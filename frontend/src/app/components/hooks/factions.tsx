import { useEffect, useState } from "react";
import axios from "axios";

import { useAuth } from "../../utils/authprovider";

import type { FactionsHook, FactionType } from "../../types/factions";

export function useFactions(): FactionsHook {
    const { token } = useAuth();

    const [factions, setFactions] = useState<FactionType[] | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!token) return;

        const fetchFactions = async () => {
            try {
                setLoading(true);
                const res = await axios.get<FactionType[]>("../factions/list");
                setFactions(res.data);
            } catch (err: any) {
                console.error("Error fetching factions:", err);
                setError(err.message || "Failed to fetch facions");
            } finally {
                setLoading(false);
            }
        };

        fetchFactions();
    }, [token]);

    return { factions, loading, error };
}
