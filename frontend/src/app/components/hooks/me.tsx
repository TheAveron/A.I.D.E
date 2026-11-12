import { useApiGet } from "../../utils/useapiget";

import type { UserHook, UserType } from "../../types/users";

export function useMe(): UserHook {
    const { data, loading, error } = useApiGet<UserType>(
        "/users/me",
        "Failed to fetch me",
    );

    return { user: data, loading, error };
}
