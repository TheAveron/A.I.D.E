import { useEffect, useState } from "react";
import axios from "axios";
import { useAuth } from "../../utils/authprovider";
import { type UserType } from "../../types/users";

export function useMe() {
    const { token } = useAuth();
    const [user, setUser] = useState<UserType | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!token) return;
        const fetchProfile = async () => {
            try {
                setLoading(true);
                const res = await axios.get<UserType>(
                    "http://127.0.0.1:8000/users/me",
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );
                setUser(res.data);
            } catch (error) {
                console.error("Error fetching me:", error, token);
            } finally {
                setLoading(false);
            }
        };

        fetchProfile();
    }, [token]);

    return { user, loading };
}
