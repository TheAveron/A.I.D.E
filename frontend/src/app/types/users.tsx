export interface UserType {
    user_id: number;
    username: string;
    is_admin: boolean;
    email: string | null;
    created_at: string;
    faction_id: number | null;
    role_id: number | null;
}
