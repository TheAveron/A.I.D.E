import type { UseFormReturn } from "react-hook-form";
import type { HookForm, HookResult } from "./hooks";

export interface FactionFormData {
    name: string;
    description: string | null;
    is_approved: boolean;
}

export interface FactionType extends FactionFormData {
    faction_id: number;
    created_at: string;
}

export interface FactionHook extends HookResult {
    faction: FactionType | null;
}

export interface FactionsHook extends HookResult {
    factions: FactionType[] | null;
}

export interface FactionFormHook extends HookForm {
    form: UseFormReturn<FactionFormData, any, FactionFormData>;
}
