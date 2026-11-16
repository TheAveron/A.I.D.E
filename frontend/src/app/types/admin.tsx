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
