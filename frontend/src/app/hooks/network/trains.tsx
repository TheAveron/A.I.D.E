import { useApiGet } from "../../utils/useapiget";

import type {
    LineType,
    TrainFilters,
    TrainHistoryType,
    TrainType,
} from "../../types/trains";

// The server returns at most 200 trains per request.
const PAGE = 200;

export function trainsUrl(filters: TrainFilters = {}): string {
    const params = new URLSearchParams({ limit: String(PAGE) });
    if (filters.line) params.set("line", filters.line);
    if (filters.service) params.set("service", filters.service);
    if (filters.q?.trim()) params.set("q", filters.q.trim());
    if (filters.includeRetired) params.set("include_retired", "true");
    if (filters.ownerUserId) {
        params.set("owner_user_id", String(filters.ownerUserId));
    }
    if (filters.ownerFactionId) {
        params.set("owner_faction_id", String(filters.ownerFactionId));
    }
    return `/trains?${params.toString()}`;
}

/** The trains matching the filters; `enabled` false requests nothing. */
export function useTrains(filters: TrainFilters = {}, enabled = true) {
    const { data, loading, error, refresh } = useApiGet<TrainType[]>(
        enabled ? trainsUrl(filters) : null,
        "Erreur lors du chargement des trains",
    );
    return { trains: data ?? [], loading, error, refresh };
}

export function useTrain(trainId: string | undefined) {
    const { data, loading, error, refresh } = useApiGet<TrainType>(
        trainId ? `/trains/${trainId}` : null,
        "Erreur lors du chargement du train",
    );
    return { train: data, loading, error, refresh };
}

export function useTrainHistory(trainId: string | undefined) {
    const { data, loading, error, refresh } = useApiGet<TrainHistoryType[]>(
        trainId ? `/trains/${trainId}/history` : null,
        "Erreur lors du chargement de l'historique",
    );
    return { history: data ?? [], loading, error, refresh };
}

export function useLines() {
    const { data, loading, error, refresh } = useApiGet<LineType[]>(
        "/lines",
        "Erreur lors du chargement des lignes",
    );
    return { lines: data ?? [], loading, error, refresh };
}
