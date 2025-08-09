import type { UseFormReturn } from "react-hook-form";

export interface HookResult {
    loading: boolean;
    error: string | null;
}

export interface HookFormBase {
    form: UseFormReturn<any>;
    loading: boolean;
    message: string;
    onSubmit: (e?: React.BaseSyntheticEvent) => Promise<void>;
}

export interface HookForm extends HookFormBase {
    isOpen: boolean;
    setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

export interface AuthType {
    access_token: string;
    token_type: string;
    user_id: number;
    username: number;
}
