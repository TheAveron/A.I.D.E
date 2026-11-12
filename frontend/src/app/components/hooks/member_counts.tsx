import { useApiGet } from "../../utils/useapiget";

/** Number of members of every faction, by faction id, in a single request. */
export function useMemberCounts(): {
    counts: Record<string, number>;
    loading: boolean;
} {
    const { data, loading } = useApiGet<Record<string, number>>(
        "/factions/member_counts",
        "Error fetching member counts",
    );

    return { counts: data ?? {}, loading };
}
