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
            currencyId: number,
            total: number,
            notes: string,
        ): Promise<CurrencyType | null> => {
            setLoading(true);
            setError(null);
            try {
                const res = await axios.put<CurrencyType>(
                    `/currencies/update/${currencyId}`,
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

    /** Change the name and/or symbol (offers and transactions follow). */
    const updateInfo = useCallback(
        async (
            currencyId: number,
            changes: { name?: string; symbol?: string },
        ): Promise<CurrencyType | null> => {
            setLoading(true);
            setError(null);
            try {
                const res = await axios.put<CurrencyType>(
                    `/currencies/update/${currencyId}`,
                    changes,
                );
                return res.data;
            } catch (err) {
                setError(getErrorMessage(err));
                return null;
            } finally {
                setLoading(false);
            }
        },
        [],
    );

    /** Delete a currency nothing refers to (offers, transactions) any more. */
    const remove = useCallback(async (currencyId: number): Promise<boolean> => {
        setLoading(true);
        setError(null);
        try {
            await axios.delete(`/currencies/delete/${currencyId}`);
            return true;
        } catch (err) {
            setError(getErrorMessage(err));
            return false;
        } finally {
            setLoading(false);
        }
    }, []);

    return { updateTotal, updateInfo, remove, loading, error };
}
