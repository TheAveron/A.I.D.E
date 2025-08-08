import { useMembers } from "../hooks/factionmembers";

import { useState, useEffect } from "react";
import { fetchMembersCount } from "../hooks/members_count";
import { useAuth } from "../../utils/authprovider";
import type { FactionType } from "../../types/factions";

function MemberCounter({ faction_id }: { faction_id: string }) {
    const { users } = useMembers(faction_id);

    return <span className="amount">{users?.length}</span>;
}

export default MemberCounter;

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
                        faction.faction_id.toString()
                    );
                    results[faction.faction_id] = count;
                })
            );
            setCounts(results);
            setLoading(false);
        };

        fetchAll();
    }, [factions, token]);

    return { counts, loading };
}
