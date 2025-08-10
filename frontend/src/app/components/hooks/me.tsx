import { useEffect, useState } from "react";
import axios from "axios";

import { useAuth } from "../../utils/authprovider";

import type { UserHook, UserType } from "../../types/users";

export function useMe(): UserHook {
    const { token } = useAuth();

    const [user, setUser] = useState<UserType | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!token) return;
        const fetchProfile = async () => {
            try {
                setLoading(true);
                const res = await axios.get<UserType>("/users/me", {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
                setUser(res.data);
            } catch (err: any) {
                console.error("Error fetching me:", err);
                setError(err.message || "Failed to fetch me");
            } finally {
                setLoading(false);
            }
        };

        fetchProfile();
    }, [token]);

    return { user, loading, error };
}
