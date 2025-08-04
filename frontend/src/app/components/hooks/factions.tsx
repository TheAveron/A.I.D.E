import { useEffect, useState } from "react";
import axios from "axios";
import { useAuth } from "../../utils/authprovider";
import { type FactionType } from "../../types/factions";

export function useFactions() {
    const { token } = useAuth();
    const [factions, setFactions] = useState<FactionType[] | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!token) return;

        const fetchFactions = async () => {
            try {
                setLoading(true);
                const res = await axios.get<FactionType[]>(
                    "http://127.0.0.1:8000/factions/list"
                );
                setFactions(res.data);
            } catch (error) {
                console.error("Error fetching faction:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchFactions();
    }, [token]);

    return { factions, loading };
}
