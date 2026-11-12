import { useApiGet } from "../../utils/useapiget";

import type { RolesHook, RoleType } from "../../types/roles";

export function useRoles(faction_id: string | null): RolesHook {
    const { data, loading, error } = useApiGet<RoleType[]>(
        faction_id ? `/roles/faction/${encodeURIComponent(faction_id)}` : null,
        "Error fetching roles",
    );

    return { roles: data, loading, error };
}
