import { useEffect, useState } from "react";
import axios from "axios";
import { useAuth } from "../../utils/authprovider";
import { type CurrencyType } from "../../types/currency";

export function useCurrency(faction_id: string | null) {
    const { token } = useAuth();
    const [currency, setCurrency] = useState<CurrencyType | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!token || !faction_id) return;

        const fetchCurrency = async () => {
            try {
                setLoading(true);
                const res = await axios.get<CurrencyType>(
                    `http://127.0.0.1:8000/currencies/faction/${faction_id}`,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );
                setCurrency(res.data);
            } catch (error) {
                console.error("Error fetching currency:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchCurrency();
    }, [token, faction_id]);

    return { currency, loading };
}
