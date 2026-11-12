import { useCallback, useState } from "react";
import axios from "axios";

import { useAuth } from "../../utils/authcontext";
import { useApiGet } from "../../utils/useapiget";

import type { RoleHook, RoleType } from "../../types/roles";

import type { UserType } from "../../types/users";

export function useRole(role_id: number | null): RoleHook {
    const { data, loading, error } = useApiGet<RoleType>(
        role_id ? `/roles/detail/${role_id}` : null,
        "Error fetching role",
    );

    return { role: data, loading, error };
}

interface UpdateUserPayload {
    faction_id?: number | null;
    role_id?: number | null;
}

interface UseUpdateUserHook {
    updateUser: (
        userId: number | null,
        data: UpdateUserPayload,
    ) => Promise<UserType | null>;
    loading: boolean;
    error: string | null;
}

export function useUpdateUser(): UseUpdateUserHook {
    const { token } = useAuth();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const updateUser = useCallback(
        async (
            userId: number | null,
            data: UpdateUserPayload,
        ): Promise<UserType | null> => {
            if (!token) {
                setError("No authentication token");
                return null;
            }

            if (!userId) {
                setError("No User Id provided");
                return null;
            }

            try {
                setLoading(true);
                setError(null);

                const res = await axios.patch<UserType>(
                    `../users/update/${userId}`,
                    {
                        faction_id: data.faction_id ?? null,
                        role_id: data.role_id ?? null,
                    },
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    },
                );

                return res.data;
            } catch (err) {
                setError(`Error updating user: ${err}`);
                return null;
            } finally {
                setLoading(false);
            }
        },
        [token],
    );

    return { updateUser, loading, error };
}
