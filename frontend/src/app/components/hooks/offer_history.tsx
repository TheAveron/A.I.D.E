import { useMemo } from "react";

import { useApiGet } from "../../utils/useapiget";

import type { OfferHistoriesHook, OfferHistoryType } from "../../types/history";

// The server returns 50 entries unless asked for more (up to 500); the table paginates what it receives, so ask for as many as possible.
const MAX_ENTRIES = "500";

export function useOfferHistoriesByActor({
    actorFactionId = null,
    actorUserId = null,
    offer_id = null,
}: {
    actorFactionId?: string | null;
    actorUserId?: string | null;
    offer_id?: string | null;
}): OfferHistoriesHook {
    const query = useMemo(() => {
        const params = new URLSearchParams({ limit: MAX_ENTRIES });
        if (actorFactionId !== null) {
            params.append("actor_faction_id", actorFactionId);
        }
        if (actorUserId !== null) params.append("actor_user_id", actorUserId);
        if (offer_id !== null) params.append("offer_id", offer_id);
        return params.toString();
    }, [actorFactionId, actorUserId, offer_id]);

    const { data, loading, error } = useApiGet<OfferHistoryType[]>(
        `/history?${query}`,
        "Error fetching offer histories",
    );

    return { offerHistories: data, loading, error };
}
