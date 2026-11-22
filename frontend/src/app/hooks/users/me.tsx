import { useApiGet } from "../../utils/useapiget";

import type { UserHook, UserType } from "../../types/users";

export function useMe(): UserHook {
    const { data, loading, error, refresh } = useApiGet<UserType>(
        "/users/me",
        "Impossible de charger votre compte",
    );

    return { user: data, loading, error, refresh };
}
