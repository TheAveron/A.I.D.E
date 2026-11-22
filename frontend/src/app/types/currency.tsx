import type { HookForm, HookResult } from "./hooks";

export interface CurrencyForm {
    name: string;
    symbol: string | null;
    total_in_circulation: number;
}

/** A faction using a currency; the issuers run it. */
export interface CurrencyFactionType {
    faction_id: number;
    faction_name: string | null;
    is_issuer: boolean;
    joined_at: string;
}

/**
 * A currency. The total in circulation (and the dates) only come to the
 * members of the factions using it, and to money admins.
 */
export interface CurrencyType {
    currency_id: number;
    name: string;
    symbol: string | null;
    factions: CurrencyFactionType[];
    // Whether the caller may change it (issuer manager, money admin)
    can_manage: boolean;
    total_in_circulation?: number;
    created_at?: string;
    updated_at?: string;
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
    currency_id: number;
    currency_name: string | null;
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

/**
 * A pending wish to have a faction use a currency: the faction asked
 * ("REQUEST", an issuer accepts) or an issuer proposed ("INVITATION", the
 * faction accepts).
 */
export interface CurrencyLinkRequestType {
    request_id: number;
    currency_id: number;
    currency_name: string | null;
    faction_id: number;
    faction_name: string | null;
    kind: "REQUEST" | "INVITATION";
    status: string;
    created_by_user_id: number | null;
    created_at: string;
}
