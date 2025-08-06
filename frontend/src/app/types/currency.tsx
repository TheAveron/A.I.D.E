import type { UseFormReturn } from "react-hook-form";
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
}

export interface CurrencyFormHook extends HookForm {
    form: UseFormReturn<CurrencyForm, any, CurrencyForm>;
}

export interface CurrencyCreateData extends CurrencyForm {
    faction_id: number | null;
}
