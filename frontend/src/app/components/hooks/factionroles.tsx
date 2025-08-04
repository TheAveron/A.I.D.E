import { useEffect, useState } from "react";
import axios from "axios";
import { useAuth } from "../../utils/authprovider";
import { type RoleType } from "../../types/roles";

export function useRoles(faction_id: string | null) {
    const { token } = useAuth();
    const [roles, setRoles] = useState<RoleType[] | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!token || !faction_id) return;

        const fetchRoles = async () => {
            try {
                setLoading(true);
                const res = await axios.get<RoleType[]>(
                    `http://127.0.0.1:8000/roles/faction/${faction_id}`
                );
                setRoles(res.data);
            } catch (error) {
                console.error("Error fetching role:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchRoles();
    }, [token, faction_id]);

    return { roles, loading };
}
