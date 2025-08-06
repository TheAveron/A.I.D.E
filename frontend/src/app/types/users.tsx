import type { UseFormReturn } from "react-hook-form";
import type { HookForm, HookResult } from "./hooks";

export interface UserBase {
    username: string;
}

export interface UserType extends UserBase {
    user_id: number;
    is_admin: boolean;
    email: string | null;
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

export interface UserRegisterData extends UserLoginForm {
    is_admin: boolean;
}

export interface UserHook extends HookResult {
    user: UserType | null;
}

export interface UsersHook extends HookResult {
    users: UserType[] | null;
}

export interface AuthLoginHook extends HookForm {
    form: UseFormReturn<UserLoginForm, any, UserLoginForm>;
}

export interface AuthRegisterHook extends HookForm {
    form: UseFormReturn<UserRegisterForm, any, UserRegisterForm>;
}
