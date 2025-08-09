import { useEffect, useState } from "react";
import axios from "axios";

import { useAuth } from "../../utils/authprovider";

import type { UserHook, UserType } from "../../types/users";

export function useUser(user_id: string | null): UserHook {
    const { token } = useAuth();

    const [user, setUser] = useState<UserType | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!token || !user_id) return;

        const fetchUser = async () => {
            try {
                setLoading(true);
                const res = await axios.get<UserType>(
                    `../users/detail/${user_id}`
                );
                setUser(res.data);
            } catch (error) {
                setError(`Error fetching currency: ${error}`);
            } finally {
                setLoading(false);
            }
        };

        fetchUser();
    }, [token, user_id]);

    return { user, loading, error };
}
