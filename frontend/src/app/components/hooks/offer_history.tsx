import { useEffect, useState, useMemo } from "react";

import axios from "axios";

import { useAuth } from "../../utils/authprovider";

import type { OfferHistoriesHook, OfferHistoryType } from "../../types/history";

export function useOfferHistoriesByActor({
    actorFactionId = null,
    actorUserId = null,
    offer_id = null,
}: {
    actorFactionId?: string | null;
    actorUserId?: string | null;
    offer_id?: string | null;
}): OfferHistoriesHook {
    const { token } = useAuth();

    const [offerHistories, setOfferHistories] = useState<
        OfferHistoryType[] | null
    >(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Build query string with URLSearchParams & useMemo
    const query = useMemo(() => {
        const params = new URLSearchParams();
        if (actorFactionId !== null && actorFactionId !== undefined) {
            params.append("actor_faction_id", actorFactionId);
        }
        if (actorUserId !== null && actorUserId !== undefined) {
            params.append("actor_user_id", actorUserId);
        }
        if (offer_id !== null && offer_id !== undefined) {
            params.append("actor_user_id", offer_id);
        }
        return params.toString();
    }, [actorFactionId, actorUserId]);

    useEffect(() => {
        if (!token) return;

        const fetchOfferHistories = async () => {
            try {
                setLoading(true);

                const res = await axios.get<OfferHistoryType[]>(
                    `http://127.0.0.1:8000/history?${query}`
                );

                setOfferHistories(res.data);
            } catch (err) {
                setError(`Error fetching offer histories: ${err}`);
            } finally {
                setLoading(false);
            }
        };

        fetchOfferHistories();
    }, [token, query]);

    return { offerHistories, loading, error };
}
