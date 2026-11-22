import type { CurrencyFactionType } from "./currency";

export interface AuditEntryType {
    log_id: number;
    actor_user_id: number | null;
    actor_name: string;
    action: string;
    target_type: string;
    target_id: number | null;
    target_name: string | null;
    detail: string | null;
    created_at: string;
}

export interface AdminUserType {
    user_id: number;
    username: string;
    email: string | null;
    faction_id: number | null;
    faction_name: string | null;
    role_id: number | null;
    role_name: string | null;
    global_roles: string[];
    created_at: string;
}

export interface AdminFactionType {
    faction_id: number;
    name: string;
    is_approved: boolean;
    requires_approval: boolean;
    member_count: number;
    created_at: string;
    deleted_at: string | null;
}

export type FactionState = "all" | "pending" | "approved" | "archived";

export type OfferState = "all" | "open" | "closed" | "cancelled";
export type TransactionState = "all" | "active" | "cancelled";

export interface AdminOfferType {
    offer_id: number;
    offer_type: "BUY" | "SELL";
    item_description: string;
    currency_name: string;
    price_per_unit: number;
    quantity: number;
    init_quantity: number;
    status: "OPEN" | "CLOSED" | "CANCELLED";
    is_private: boolean;
    owner_kind: "user" | "faction";
    owner_id: number | null;
    owner_name: string | null;
    expires_at: string | null;
    created_at: string;
}

export interface AdminTransactionType {
    transaction_id: number;
    offer_id: number;
    item_description: string;
    buyer_name: string | null;
    seller_name: string | null;
    amount: number;
    currency_name: string;
    quantity: number | null;
    timestamp: string;
    cancelled_at: string | null;
    cancelled_by_name: string | null;
    cancel_reason: string | null;
}

export interface AdminTransactionCancelled {
    transaction: AdminTransactionType;
    quantity_restored: boolean;
    offer_reopened: boolean;
}

export interface AdminCurrencyType {
    currency_id: number;
    name: string;
    symbol: string | null;
    factions: CurrencyFactionType[];
    total_in_circulation: number;
    created_at: string;
}

export interface AdminUserState {
    user: AdminUserType;
    token_version: number;
    offers_by_status: Record<string, number>;
    purchases: number;
    sales: number;
    unread_notifications: number;
    pending_join_request: string | null;
    trains_owned: number;
}

export interface AdminFactionState {
    faction: AdminFactionType;
    description: string | null;
    leader: string | null;
    roles: { name: string; member_count: number }[];
    currency: AdminCurrencyType | null;
    offers_by_status: Record<string, number>;
    pending_join_requests: number;
    trains_owned: number;
}
