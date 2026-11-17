import axios from "axios";
import { useCallback, useState } from "react";

import { getErrorMessage } from "../../utils/apierror";
import { useApiGet } from "../../utils/useapiget";
import type { JoinRequestType } from "../../types/joinrequests";

/** The logged-in user's open request to join a faction, if any. */
export function useMyJoinRequest() {
    const { data, loading, error, refresh } = useApiGet<JoinRequestType | null>(
        "/join_requests/mine",
        "Error fetching your join request",
    );

    return { request: data, loading, error, refresh };
}

/**
 * Open requests to join a faction. Only the members who manage members of
 * that faction may ask (anybody else gets a 403): pass null for the others.
 */
export function useFactionJoinRequests(factionId: string | null) {
    const { data, loading, error, refresh } = useApiGet<JoinRequestType[]>(
        factionId
            ? `/join_requests/faction/${encodeURIComponent(factionId)}`
            : null,
        "Error fetching join requests",
    );

    return { requests: data ?? [], loading, error, refresh };
}

/** The actions on join requests; each one resolves to true on success. */
export function useJoinRequestActions() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const run = useCallback(
        async (action: () => Promise<unknown>): Promise<boolean> => {
            setLoading(true);
            setError(null);
            try {
                await action();
                return true;
            } catch (err) {
                setError(getErrorMessage(err));
                return false;
            } finally {
                setLoading(false);
            }
        },
        [],
    );

    const create = useCallback(
        (factionId: number, message?: string) =>
            run(() =>
                axios.post("/join_requests", {
                    faction_id: factionId,
                    message: message?.trim() || null,
                }),
            ),
        [run],
    );
    const accept = useCallback(
        (requestId: number) =>
            run(() => axios.post(`/join_requests/${requestId}/accept`)),
        [run],
    );
    const refuse = useCallback(
        (requestId: number) =>
            run(() => axios.post(`/join_requests/${requestId}/refuse`)),
        [run],
    );
    const withdraw = useCallback(
        (requestId: number) =>
            run(() => axios.delete(`/join_requests/${requestId}`)),
        [run],
    );

    return { create, accept, refuse, withdraw, loading, error };
}
