import type { HookResult } from "./hooks";

export interface TransactionType {
    offer_id: number;
    buyer_user_id?: number | null;
    buyer_faction_id?: number | null;
    amount: number;
    currency_name: string;
    transaction_id: number;
    timestamp: string;
}

export interface TransactionHook extends HookResult {
    transaction: TransactionType | null;
}

export interface TransactionsHook extends HookResult {
    transactions: TransactionType[] | null;
}
