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
    manage_trains: boolean;
    manage_territory: boolean;
    view_transactions: boolean;
    role_id: number;
    faction_id: number;
}

export interface RoleHook extends HookResult {
    role: RoleType | null;
}

export interface RolesHook extends HookResult {
    roles: RoleType[] | null;
    refresh: () => void;
}

export const ROLE_PERMISSIONS = [
    ["view_transactions", "Voir les transactions"],
    ["accept_offers", "Accepter les offres"],
    ["create_offers", "Créer des offres"],
    ["manage_funds", "Gérer la monnaie"],
    ["manage_docs", "Gérer les documents"],
    ["manage_trains", "Gérer les trains"],
    ["manage_territory", "Gérer les territoires et points de la carte"],
    ["handle_members", "Gérer les membres"],
    ["manage_roles", "Gérer les rôles"],
] as const;

export type RolePermission = (typeof ROLE_PERMISSIONS)[number][0];
