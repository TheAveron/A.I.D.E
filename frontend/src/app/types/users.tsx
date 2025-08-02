export interface UserProfile {
    user_id: number;
    username: string;
    is_admin: boolean;
    email: string | null;
    created_at: string; // ISO datetime string from backend
    faction_id: number | null;
    role_id: number | null;
}
