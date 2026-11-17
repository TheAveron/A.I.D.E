import { useApiGet } from "../../utils/useapiget";

import type {
    AdminCurrencyType,
    AdminFactionType,
    AdminOfferType,
    AdminTransactionType,
    AdminUserType,
    AuditEntryType,
    FactionState,
    OfferState,
    TransactionState,
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

function pagedParams(
    search: string,
    page: number,
    extra: Record<string, string>,
) {
    const params = new URLSearchParams({
        limit: String(ADMIN_PAGE),
        skip: String((page - 1) * ADMIN_PAGE),
        ...extra,
    });
    if (search.trim()) params.set("q", search.trim());
    return params.toString();
}

export function useAdminOffers(
    state: OfferState,
    search: string,
    page: number,
) {
    const { data, loading, error, refresh } = useApiGet<AdminOfferType[]>(
        `/admin/offers?${pagedParams(search, page, { state })}`,
        "Erreur lors du chargement des offres",
    );
    return { offers: data ?? [], loading, error, refresh };
}

export function useAdminTransactions(
    state: TransactionState,
    search: string,
    page: number,
) {
    const { data, loading, error, refresh } = useApiGet<AdminTransactionType[]>(
        `/admin/transactions?${pagedParams(search, page, { state })}`,
        "Erreur lors du chargement des transactions",
    );
    return { transactions: data ?? [], loading, error, refresh };
}

export function useAdminCurrencies() {
    const { data, loading, error, refresh } = useApiGet<AdminCurrencyType[]>(
        "/admin/currencies",
        "Erreur lors du chargement des monnaies",
    );
    return { currencies: data ?? [], loading, error, refresh };
}
