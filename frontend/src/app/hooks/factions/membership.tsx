import axios from "axios";
import { useCallback, useState } from "react";

import { getErrorMessage } from "../../utils/apierror";

/** Leaving one's own faction, or removing a member (needs handle_members). */
export function useMembership() {
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

    const leave = useCallback(
        () => run(() => axios.post("/users/leave")),
        [run],
    );
    const kick = useCallback(
        (userId: number) => run(() => axios.post(`/users/${userId}/kick`)),
        [run],
    );

    return { leave, kick, loading, error };
}
