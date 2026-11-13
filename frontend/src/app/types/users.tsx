import type { HookFormBase, HookResult } from "./hooks";

export interface UserBase {
    username: string;
}

export interface UserType extends UserBase {
    user_id: number;
    is_admin: boolean;
    // Only present on your own profile (/users/me)
    email?: string | null;
    created_at: string;
    faction_id: number | null;
    role_id: number | null;
}

export interface UserLoginForm extends UserBase {
    password: string;
}

export interface UserRegisterForm extends UserLoginForm {
    cpassword: string;
}

// What /auth/register accepts: nothing more than the credentials (admins are
// created on the server, never through the API).
export type UserRegisterData = UserLoginForm;

export interface UserHook extends HookResult {
    user: UserType | null;
    refresh: () => void;
}

export interface UsersHook extends HookResult {
    users: UserType[] | null;
    refresh: () => void;
}

export type AuthLoginHook = HookFormBase<UserLoginForm>;

export type AuthRegisterHook = HookFormBase<UserRegisterForm>;
