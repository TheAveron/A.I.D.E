import axios from "axios";
import { useCallback, useEffect, useState } from "react";

import { getErrorMessage } from "../../utils/apierror";
import { useApiGet } from "../../utils/useapiget";
import type { NotificationType } from "../../types/notifications";

const POLL_MS = 60_000;

/** How many notifications are unread; checked again every minute while the tab is visible. */
export function useUnreadCount(poll = true) {
    const { data, refresh } = useApiGet<{ count: number }>(
        "/notifications/unread_count",
        "Impossible de charger les notifications",
    );

    useEffect(() => {
        if (!poll) return;
        const timer = setInterval(() => {
            if (document.visibilityState === "visible") refresh();
        }, POLL_MS);
        return () => clearInterval(timer);
    }, [poll, refresh]);

    return { count: data?.count ?? 0, refresh };
}

export function useNotifications() {
    const { data, loading, error, refresh } = useApiGet<NotificationType[]>(
        "/notifications?limit=100",
        "Impossible de charger les notifications",
    );
    return { notifications: data ?? [], loading, error, refresh };
}

/** Marking notifications as read; the count and the list reload after it. */
export function useNotificationActions() {
    const { refresh: refreshList } = useNotifications();
    const { refresh: refreshCount } = useUnreadCount(false);
    const [error, setError] = useState<string | null>(null);

    const run = useCallback(
        async (action: () => Promise<unknown>) => {
            setError(null);
            try {
                await action();
                refreshList();
                refreshCount();
            } catch (err) {
                setError(getErrorMessage(err));
            }
        },
        [refreshList, refreshCount],
    );

    const markRead = useCallback(
        (id: number) => run(() => axios.post(`/notifications/${id}/read`)),
        [run],
    );
    const markAllRead = useCallback(
        () => run(() => axios.post("/notifications/read_all")),
        [run],
    );

    return { markRead, markAllRead, error };
}
