import { useApiGet } from "../../utils/useapiget";

import type { RolesHook, RoleType } from "../../types/roles";

export function useRoles(faction_id: string | null): RolesHook {
    const { data, loading, error, refresh } = useApiGet<RoleType[]>(
        faction_id ? `/roles/faction/${encodeURIComponent(faction_id)}` : null,
        "Impossible de charger les rôles",
    );

    return { roles: data, loading, error, refresh };
}
