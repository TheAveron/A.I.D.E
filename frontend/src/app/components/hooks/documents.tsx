import { useApiGet } from "../../utils/useapiget";
import type { DocumentSummaryType } from "../../types/documents";

/** The documents written by a faction (public, like reading them). */
export function useFactionDocuments(factionId: string | null) {
    const { data, loading, error, refresh } = useApiGet<DocumentSummaryType[]>(
        factionId
            ? `/documents/faction/${encodeURIComponent(factionId)}`
            : null,
        "Error fetching documents",
    );

    return { documents: data ?? [], loading, error, refresh };
}
