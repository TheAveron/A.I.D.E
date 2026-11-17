import { useApiGet } from "../../utils/useapiget";

import type { StationType } from "../../types/trains";

/** The stations matching a search (the server returns at most 200). */
export function useStations(search = "", dimension = "") {
    const params = new URLSearchParams({ limit: "200" });
    if (search.trim()) params.set("q", search.trim());
    if (dimension) params.set("dimension", dimension);

    const { data, loading, error, refresh } = useApiGet<StationType[]>(
        `/stations?${params.toString()}`,
        "Erreur lors du chargement des gares",
    );
    return { stations: data ?? [], loading, error, refresh };
}

export function useStation(stationId: string | undefined) {
    const { data, loading, error, refresh } = useApiGet<StationType>(
        stationId ? `/stations/${stationId}` : null,
        "Erreur lors du chargement de la gare",
    );
    return { station: data, loading, error, refresh };
}
