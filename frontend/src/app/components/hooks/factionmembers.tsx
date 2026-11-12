import { useApiGet } from "../../utils/useapiget";

import type { UsersHook, UserType } from "../../types/users";

export function useMembers(faction_id: string | null): UsersHook {
    const { data, loading, error, refresh } = useApiGet<UserType[]>(
        faction_id ? `/users/faction/${encodeURIComponent(faction_id)}` : null,
        "Error fetching faction members",
    );

    return { users: data, loading, error, refresh };
}
