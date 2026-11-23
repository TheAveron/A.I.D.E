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
    const [retryKey, setRetryKey] = useState(0);
    // The answer remembers which attempt it belongs to: while it is not the
    // current one, the list is loading (no state reset at the start of the
    // effect). The last list stays shown during a retry and after a failure.
    const [result, setResult] = useState<{
        key: number;
        factions: FactionDocumentsType[];
        error: string;
    } | null>(null);
    const loading = result?.key !== retryKey;

    useEffect(() => {
        const controller = new AbortController();
        fetch("/documents/factions", { signal: controller.signal })
            .then(async (response) => {
                if (!response.ok) throw new Error(String(response.status));
                const factions: FactionDocumentsType[] = await response.json();
                setResult({ key: retryKey, factions, error: "" });
            })
            .catch((err) => {
                if (err instanceof DOMException && err.name === "AbortError") {
                    return;
                }
                setResult((previous) => ({
                    key: retryKey,
                    factions: previous?.factions ?? [],
                    error: "Impossible de charger les documents des factions.",
                }));
            });
        return () => controller.abort();
    }, [retryKey]);

    return {
        factions: result?.factions ?? [],
        loading,
        error: !loading && result ? result.error : "",
        retry: () => setRetryKey((key) => key + 1),
    };
}
