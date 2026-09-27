import type { FieldValues, UseFormReturn } from "react-hook-form";

export interface HookResult {
    loading: boolean;
    error: string | null;
}

export interface HookFormBase<TFieldValues extends FieldValues = FieldValues> {
    form: UseFormReturn<TFieldValues, unknown, TFieldValues>;
    loading: boolean;
    message: string;
    onSubmit: (e?: React.BaseSyntheticEvent) => Promise<void>;
}

export interface HookForm<
    TFieldValues extends FieldValues = FieldValues,
> extends HookFormBase<TFieldValues> {
    isOpen: boolean;
    setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

export interface AuthType {
    access_token: string;
    token_type: string;
    user_id: number;
    username: number;
}
