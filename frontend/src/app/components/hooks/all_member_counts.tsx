import { useEffect, useState } from "react";
import { fetchMembersCount } from "./members_count";
import { useAuth } from "../../utils/authcontext";
import type { FactionType } from "../../types/factions";

export function useAllMemberCounts(factions: FactionType[] | null) {
    const { token } = useAuth();
    const [counts, setCounts] = useState<Record<string, number>>({});
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!factions || !token) return;

        const fetchAll = async () => {
            setLoading(true);
            const results: Record<string, number> = {};
            await Promise.all(
                factions.map(async (faction) => {
                    const count = await fetchMembersCount(
                        faction.faction_id.toString(),
                    );
                    results[faction.faction_id] = count;
                }),
            );
            setCounts(results);
            setLoading(false);
        };

        fetchAll();
    }, [factions, token]);

    return { counts, loading };
}
