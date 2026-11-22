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
    // The offer it came from (sent with it, not fetched row by row)
    offer_item_description?: string | null;
    offer_user_id?: number | null;
    offer_faction_id?: number | null;
}

export interface TransactionHook extends HookResult {
    transaction: TransactionType | null;
}

export interface TransactionsHook extends HookResult {
    transactions: TransactionType[] | null;
}
