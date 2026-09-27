import { useEffect, useState } from "react";
import axios from "axios";

import { useAuth } from "../../utils/authcontext";

import type { FactionsHook, FactionType } from "../../types/factions";

export function useFactions(): FactionsHook {
    const { token } = useAuth();

    const [factions, setFactions] = useState<FactionType[] | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [refreshKey, setRefreshKey] = useState(0);

    useEffect(() => {
        if (!token) return;

        const fetchFactions = async () => {
            try {
                setLoading(true);
                setError(null);
                const res = await axios.get<FactionType[]>("/factions/list");
                setFactions(res.data);
            } catch (err: unknown) {
                console.error("Error fetching factions:", err);
                setError(
                    axios.isAxiosError(err)
                        ? err.message
                        : "Failed to fetch factions",
                );
            } finally {
                setLoading(false);
            }
        };

        fetchFactions();
    }, [token, refreshKey]);

    return {
        factions,
        loading,
        error,
        refresh: () => setRefreshKey((value) => value + 1),
    };
}
