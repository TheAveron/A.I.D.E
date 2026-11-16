import { useApiGet } from "../../utils/useapiget";

import type {
    AdminFactionType,
    AdminUserType,
    AuditEntryType,
    FactionState,
} from "../../types/admin";

export const ADMIN_PAGE = 50;

export function useAuditLog(action: string, targetType: string, page: number) {
    const params = new URLSearchParams({
        limit: String(ADMIN_PAGE),
        skip: String((page - 1) * ADMIN_PAGE),
    });
    if (action) params.set("action", action);
    if (targetType) params.set("target_type", targetType);

    const { data, loading, error, refresh } = useApiGet<AuditEntryType[]>(
        `/admin/audit?${params.toString()}`,
        "Erreur lors du chargement du journal",
    );
    return { entries: data ?? [], loading, error, refresh };
}

export function useAdminUsers(search: string, role: string, page: number) {
    const params = new URLSearchParams({
        limit: String(ADMIN_PAGE),
        skip: String((page - 1) * ADMIN_PAGE),
    });
    if (search.trim()) params.set("q", search.trim());
    if (role) params.set("role", role);

    const { data, loading, error, refresh } = useApiGet<AdminUserType[]>(
        `/admin/users?${params.toString()}`,
        "Erreur lors du chargement des comptes",
    );
    return { users: data ?? [], loading, error, refresh };
}

export function useAdminFactions(state: FactionState, search: string) {
    const params = new URLSearchParams({ limit: "500", state });
    if (search.trim()) params.set("q", search.trim());

    const { data, loading, error, refresh } = useApiGet<AdminFactionType[]>(
        `/admin/factions?${params.toString()}`,
        "Erreur lors du chargement des factions",
    );
    return { factions: data ?? [], loading, error, refresh };
}
