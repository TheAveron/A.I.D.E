import { useCallback, useEffect, useState } from "react";
import axios from "axios";

import { useAuth } from "../../utils/authprovider";

import type { RoleHook, RoleType } from "../../types/roles";

import type { UserType } from "../../types/users";

export function useRole(role_id: number | null): RoleHook {
    const { token } = useAuth();

    const [role, setRole] = useState<RoleType | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!token || !role_id) return;

        const fetchRole = async () => {
            try {
                setLoading(true);
                const res = await axios.get<RoleType>(
                    `http://127.0.0.1:8000/roles/detail/${role_id}`
                );
                setRole(res.data);
            } catch (error) {
                setError(`Error fetching role: ${error}`);
            } finally {
                setLoading(false);
            }
        };

        fetchRole();
    }, [token, role_id]);

    return { role, loading, error };
}
interface UpdateUserPayload {
    faction_id?: string | null;
    role_id?: string | null;
}

interface UseUpdateUserRoleFactionHook {
    updateUser: (
        userId: number,
        data: UpdateUserPayload
    ) => Promise<UserType | null>;
    loading: boolean;
    error: string | null;
}

export function useUpdateUserRole(): UseUpdateUserRoleFactionHook {
    const { token } = useAuth();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const updateUser = useCallback(
        async (
            userId: number,
            data: UpdateUserPayload
        ): Promise<UserType | null> => {
            if (!token) {
                setError("No authentication token");
                return null;
            }

            try {
                setLoading(true);
                setError(null);

                const res = await axios.patch<UserType>(
                    `http://127.0.0.1:8000/users/update/${userId}`,
                    {
                        faction_id: data.faction_id ?? null,
                        role_id: data.role_id ?? null,
                    },
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );

                return res.data;
            } catch (err) {
                setError(`Error updating user: ${err}`);
                return null;
            } finally {
                setLoading(false);
            }
        },
        [token]
    );

    return { updateUser, loading, error };
}
