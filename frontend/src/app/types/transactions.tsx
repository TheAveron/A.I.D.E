import type { HookResult } from "./hooks";

export interface TransactionType {
    offer_id: number;
    buyer_user_id?: number | null;
    buyer_faction_id?: number | null;
    amount: number;
    currency_name: string;
    transaction_id: number;
    timestamp: string;
    quantity?: number | null;
    // Set when an admin cancelled the transaction
    cancelled_at?: string | null;
    cancel_reason?: string | null;
}

export interface TransactionHook extends HookResult {
    transaction: TransactionType | null;
}

export interface TransactionsHook extends HookResult {
    transactions: TransactionType[] | null;
}
