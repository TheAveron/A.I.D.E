import { useApiGet } from "../../utils/useapiget";

import type {
    CurrencyHistoryHook,
    CurrencyHistoryType,
} from "../../types/currency";

// The server returns 50 entries unless asked for more (up to 500); the table
// paginates what it receives.
const MAX_ENTRIES = 500;

/**
 * The audit trail of a currency's total in circulation (and of its renames),
 * newest first. Only the holders of manage_funds in a faction using the
 * currency, and money admins, may read it (anybody else gets a 403): pass
 * `null` for the others to not ask at all.
 */
export function useCurrencyHistory(
    currencyId: number | null,
): CurrencyHistoryHook {
    const { data, loading, error, refresh } = useApiGet<CurrencyHistoryType[]>(
        currencyId !== null
            ? `/currencies/history/${currencyId}?limit=${MAX_ENTRIES}`
            : null,
        "Error fetching currency history",
    );

    return { histories: data, loading, error, refresh };
}
