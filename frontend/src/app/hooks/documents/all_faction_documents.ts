import { useEffect, useState } from "react";

import type { DocumentSummaryType } from "../../types/documents";

export interface FactionDocumentsType {
    faction_id: number;
    faction_name: string;
    documents: DocumentSummaryType[];
}

/**
 * Every faction that has written documents, with them. Public: a plain fetch,
 * since useApiGet asks for nothing while nobody is logged in.
 */
export function useAllFactionDocuments() {
    const [factions, setFactions] = useState<FactionDocumentsType[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [retryKey, setRetryKey] = useState(0);

    useEffect(() => {
        const controller = new AbortController();
        setLoading(true);
        setError("");
        fetch("/documents/factions", { signal: controller.signal })
            .then(async (response) => {
                if (!response.ok) throw new Error(String(response.status));
                setFactions(await response.json());
                setLoading(false);
            })
            .catch((err) => {
                if (err instanceof DOMException && err.name === "AbortError") {
                    return;
                }
                setError("Impossible de charger les documents des factions.");
                setLoading(false);
            });
        return () => controller.abort();
    }, [retryKey]);

    return {
        factions,
        loading,
        error,
        retry: () => setRetryKey((key) => key + 1),
    };
}
