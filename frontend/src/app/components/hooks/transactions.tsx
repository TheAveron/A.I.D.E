import { useMemo } from "react";

import { useApiGet } from "../../utils/useapiget";

import type {
    TransactionHook,
    TransactionsHook,
    TransactionType,
} from "../../types/transactions";

// The server returns 100 transactions unless asked for more (up to 500); the
// table paginates what it receives.
const MAX_TRANSACTIONS = "500";

export function useTransaction(transactionId: string | null): TransactionHook {
    const { data, loading, error } = useApiGet<TransactionType>(
        transactionId
            ? `/transactions/${encodeURIComponent(transactionId)}`
            : null,
        "Error fetching transaction",
    );

    return { transaction: data, loading, error };
}

export function useTransactions({
    factionId = null,
    userId = null,
    offerId = null,
}: {
    factionId: string | null;
    userId: string | null;
    offerId: string | null;
}): TransactionsHook {
    const query = useMemo(() => {
        const params = new URLSearchParams({ limit: MAX_TRANSACTIONS });
        if (factionId !== null) params.append("faction_id", factionId);
        if (userId !== null) params.append("user_id", userId);
        if (offerId !== null) params.append("offer_id", offerId);
        return params.toString();
    }, [factionId, offerId, userId]);

    const { data, loading, error } = useApiGet<TransactionType[]>(
        `/transactions/?${query}`,
        "Error fetching transactions",
    );

    return { transactions: data, loading, error };
}
