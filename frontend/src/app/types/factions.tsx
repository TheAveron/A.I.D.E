import type { HookForm, HookResult } from "./hooks";

export interface FactionFormData {
    name: string;
    description: string | null;
    is_approved: boolean;
}

export interface FactionType extends FactionFormData {
    faction_id: number;
    created_at: string;
    // true: members are only taken through join requests
    requires_approval: boolean;
    // Set once the leader deleted the faction (it stays for past trades)
    deleted_at: string | null;
}

export interface FactionHook extends HookResult {
    faction: FactionType | null;
    refresh: () => void;
}

export interface FactionsHook extends HookResult {
    factions: FactionType[] | null;
    refresh: () => void;
}

export type FactionFormHook = HookForm<FactionFormData>;
