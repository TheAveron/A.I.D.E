import { useApiGet } from "../../utils/useapiget";

import type { FactionsHook, FactionType } from "../../types/factions";

// The server returns at most 100 factions unless asked for more (up to 500).
const FACTIONS_URL = "/factions/list?limit=500";

export function useFactions(): FactionsHook {
    const { data, loading, error, refresh } = useApiGet<FactionType[]>(
        FACTIONS_URL,
        "Failed to fetch factions",
    );

    return { factions: data, loading, error, refresh };
}
