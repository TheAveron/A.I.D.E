import { useEffect, useState } from "react";
import axios from "axios";
import { useAuth } from "../../utils/authprovider";
import { type UserType } from "../../types/users";

export function useUser(user_id: string | null) {
    const { token } = useAuth();
    const [user, setUser] = useState<UserType | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!token || !user_id) return;

        const fetchCurrency = async () => {
            try {
                setLoading(true);
                const res = await axios.get<UserType>(
                    `http://127.0.0.1:8000/users/detail/${user_id}`
                );
                setUser(res.data);
            } catch (error) {
                console.error("Error fetching currency:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchCurrency();
    }, [token, user_id]);

    return { user, loading };
}
