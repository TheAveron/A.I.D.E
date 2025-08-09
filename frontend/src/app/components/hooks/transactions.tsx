import { useEffect, useMemo, useState } from "react";

import axios from "axios";

import { useAuth } from "../../utils/authprovider";

import type {
    TransactionHook,
    TransactionsHook,
    TransactionType,
} from "../../types/transactions";

export function useTransaction(transactionId: string | null): TransactionHook {
    const { token } = useAuth();

    const [transaction, setTransactions] = useState<TransactionType | null>(
        null
    );
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!token || !transactionId) return;

        const fetchTransactions = async () => {
            try {
                setLoading(true);

                const res = await axios.get<TransactionType>(
                    `../transactions/${transactionId}`
                );

                setTransactions(res.data);
            } catch (err) {
                setError(`Error fetching transactions: ${err}`);
            } finally {
                setLoading(false);
            }
        };

        fetchTransactions();
    }, [token, transactionId]);

    return { transaction, loading, error };
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
    const { token } = useAuth();

    const [transactions, setTransactions] = useState<TransactionType[] | null>(
        null
    );
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const query = useMemo(() => {
        const params = new URLSearchParams();
        if (factionId !== null && factionId !== undefined) {
            params.append("faction_id", factionId);
        }
        if (userId !== null && userId !== undefined) {
            params.append("user_id", userId);
        }
        if (offerId !== null && offerId !== undefined) {
            params.append("offer_id", offerId);
        }
        return params.toString();
    }, [factionId, userId]);

    useEffect(() => {
        if (!token) return;

        const fetchTransactions = async () => {
            try {
                setLoading(true);

                const res = await axios.get<TransactionType[]>(
                    `../transactions/?${query}`
                );
                console.log("e", transactions);

                setTransactions(res.data);
            } catch (err) {
                setError(`Error fetching transactions: ${err}`);
            } finally {
                setLoading(false);
            }
        };

        fetchTransactions();
    }, [token, query]);

    return { transactions, loading, error };
}
