import axios from "axios";
import { useCallback, useState } from "react";

import { getErrorMessage } from "../../utils/apierror";
import type { CurrencyType } from "../../types/currency";

/** Declare a new total in circulation (the change is logged by the server). */
export function useUpdateCurrency() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const updateTotal = useCallback(
        async (
            currencyName: string,
            total: number,
            notes: string,
        ): Promise<CurrencyType | null> => {
            setLoading(true);
            setError(null);
            try {
                const res = await axios.put<CurrencyType>(
                    `/currencies/update/${encodeURIComponent(currencyName)}`,
                    {
                        total_in_circulation: total,
                        notes: notes.trim() || null,
                    },
                );
                return res.data;
            } catch (err) {
                setError(
                    `Erreur lors de la mise à jour : ${getErrorMessage(err)}`,
                );
                return null;
            } finally {
                setLoading(false);
            }
        },
        [],
    );

    return { updateTotal, loading, error };
}
