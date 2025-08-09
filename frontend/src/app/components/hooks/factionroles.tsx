import { useEffect, useState } from "react";
import axios from "axios";

import { useAuth } from "../../utils/authprovider";

import type { RolesHook, RoleType } from "../../types/roles";

export function useRoles(faction_id: string | null): RolesHook {
    const { token } = useAuth();

    const [roles, setRoles] = useState<RoleType[] | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!token || !faction_id) return;

        const fetchRoles = async () => {
            try {
                setLoading(true);
                const res = await axios.get<RoleType[]>(
                    `../roles/faction/${faction_id}`
                );
                setRoles(res.data);
            } catch (error) {
                setError(`Error fetching role: ${error}`);
            } finally {
                setLoading(false);
            }
        };

        fetchRoles();
    }, [token, faction_id]);

    return { roles, loading, error };
}
