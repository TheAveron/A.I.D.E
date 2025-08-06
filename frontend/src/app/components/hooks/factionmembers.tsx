import { useEffect, useState } from "react";
import axios from "axios";

import { useAuth } from "../../utils/authprovider";

import type { UsersHook, UserType } from "../../types/users";

export function useMembers(faction_id: string | null): UsersHook {
    const { token } = useAuth();

    const [users, setUsers] = useState<UserType[] | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!token || !faction_id) return;

        const fetchUsers = async () => {
            try {
                setLoading(true);
                const res = await axios.get<UserType[]>(
                    `http://127.0.0.1:8000/users/faction/${faction_id}`
                );
                setUsers(res.data);
            } catch (error) {
                setError(`Error fetching faction members: ${error}`);
            } finally {
                setLoading(false);
            }
        };

        fetchUsers();
    }, [token, faction_id]);

    return { users, loading, error };
}
