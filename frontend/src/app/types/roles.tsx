import type { HookResult } from "./hooks";

export interface RoleType {
    name: string;
    description: string;
    accept_offers: boolean;
    create_offers: boolean;
    manage_funds: boolean;
    handle_members: boolean;
    manage_roles: boolean;
    manage_docs: boolean;
    view_transactions: boolean;
    role_id: number;
    faction_id: number;
}

export interface RoleHook extends HookResult {
    role: RoleType | null;
}

export interface RolesHook extends HookResult {
    roles: RoleType[] | null;
}
