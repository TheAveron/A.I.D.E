import { useCallback, useEffect, useState } from "react";
import axios from "axios";

import { getErrorMessage } from "./apierror";
import { useAuth } from "./authcontext";

type Result<T> = {
    key: string;
    refreshKey: number;
    data: T | null;
    error: string | null;
};

export interface ApiGetResult<T> {
    data: T | null;
    loading: boolean;
    error: string | null;
    refresh: () => void;
}

// GETs for the same URL that are in flight at the same moment share one request: a table of 20 rows that each ask for the same user sent 20 of them. Nothing is kept once the answer has arrived, so data is never stale.
const inFlight = new Map<string, Promise<unknown>>();

// Components showing the same data (the same URL, for the same user) reload together: after joining a faction, every part of the page using /users/me must see it, not only the one that asked.
const reloaders = new Map<string, Set<() => void>>();

function sharedGet<T>(key: string, url: string): Promise<T> {
    const running = inFlight.get(key);
    if (running) return running as Promise<T>;

    const request = axios
        .get<T>(url)
        .then((res) => res.data)
        .finally(() => {
            inFlight.delete(key);
        });
    inFlight.set(key, request);

    return request;
}

/**
 * GET `url` (an absolute path such as "/users/me") for the logged-in user.
 *
 * - `url` null, or no user logged in: nothing is requested and there is no
 *   data, no error and no loading state.
 * - When the URL or the user changes, the previous answer is dropped at once
 *   (it belongs to someone else), and an answer that comes back late for a
 *   previous URL is ignored instead of overwriting the current one.
 * - `refresh()` reloads while keeping the data on screen.
 */
export function useApiGet<T>(
    url: string | null,
    errorLabel = "Erreur de chargement",
): ApiGetResult<T> {
    const { token } = useAuth();

    // The token is part of the key: another account never sees this one's data.
    const key = token && url ? `${token}\n${url}` : null;

    const [refreshKey, setRefreshKey] = useState(0);
    const [result, setResult] = useState<Result<T> | null>(null);

    useEffect(() => {
        if (key === null || url === null) return;

        let cancelled = false;

        const request =
            refreshKey === 0
                ? sharedGet<T>(key, url)
                : axios.get<T>(url).then((res) => res.data);

        request.then(
            (data) => {
                if (!cancelled) {
                    setResult({ key, refreshKey, data, error: null });
                }
            },
            (err: unknown) => {
                if (!cancelled) {
                    setResult({
                        key,
                        refreshKey,
                        data: null,
                        error: `${errorLabel}: ${getErrorMessage(err)}`,
                    });
                }
            },
        );

        return () => {
            cancelled = true;
        };
    }, [key, url, refreshKey, errorLabel]);

    useEffect(() => {
        if (key === null) return;

        const reload = () => setRefreshKey((n) => n + 1);
        const group = reloaders.get(key) ?? new Set<() => void>();
        group.add(reload);
        reloaders.set(key, group);

        return () => {
            group.delete(reload);
            if (group.size === 0) reloaders.delete(key);
        };
    }, [key]);

    const refresh = useCallback(() => {
        if (key === null) return;
        reloaders.get(key)?.forEach((reload) => reload());
    }, [key]);

    const current = result !== null && result.key === key ? result : null;
    const loading =
        key !== null && (current === null || current.refreshKey !== refreshKey);

    return {
        data: current?.data ?? null,
        loading,
        error: loading ? null : (current?.error ?? null),
        refresh,
    };
}
