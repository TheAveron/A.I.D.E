import type { HookForm, HookResult } from "./hooks";

export interface CurrencyForm {
    name: string;
    symbol: string | null;
    total_in_circulation: number;
}

export interface CurrencyType extends CurrencyForm {
    faction_id: number;
    created_at: string;
    updated_at: string;
}

export interface CurrencyHook extends HookResult {
    currency: CurrencyType | null;
    refresh: () => void;
}

export type CurrencyFormHook = HookForm<CurrencyForm>;

export interface CurrencyCreateData extends CurrencyForm {
    faction_id: number | null;
}

export interface CurrencyHistoryType {
    history_id: number;
    currency_name: string;
    actor_user_id: number | null;
    old_total_in_circulation: number;
    new_total_in_circulation: number;
    notes: string | null;
    timestamp: string;
}

export interface CurrencyHistoryHook extends HookResult {
    histories: CurrencyHistoryType[] | null;
    refresh: () => void;
}
