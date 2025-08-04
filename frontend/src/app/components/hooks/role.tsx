import { useEffect, useState } from "react";
import axios from "axios";
import { useAuth } from "../../utils/authprovider";
import { type RoleType } from "../../types/roles";

export function useRole(role_id: string | null) {
    const { token } = useAuth();
    const [role, setRole] = useState<RoleType | null>(null);
    const [loading, setLoading] = useState(true);

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
                console.error("Error fetching role:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchRole();
    }, [token, role_id]);

    return { role, loading };
}
