import { useApiGet } from "../../utils/useapiget";

import type { UserHook, UserType } from "../../types/users";

export function useUser(user_id: string | null): UserHook {
    const { data, loading, error, refresh } = useApiGet<UserType>(
        user_id ? `/users/detail/${encodeURIComponent(user_id)}` : null,
        "Error fetching user",
    );

    return { user: data, loading, error, refresh };
}
