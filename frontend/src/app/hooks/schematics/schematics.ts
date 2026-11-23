import { useEffect, useState } from "react";
import axios from "axios";

import { useApiGet } from "../../utils/useapiget";
import type {
    SchematicFilters,
    SchematicSummaryType,
    SchematicType,
    TagCountType,
} from "../../types/schematics";

const PAGE = 200;

export function schematicsUrl(filters: SchematicFilters = {}): string {
    const params = new URLSearchParams({ limit: String(PAGE) });
    if (filters.q?.trim()) params.set("q", filters.q.trim());
    for (const tag of filters.tags ?? []) params.append("tag", tag);
    if (filters.compliantOnly) params.set("compliant", "true");
    if (filters.authorUserId) {
        params.set("author_user_id", String(filters.authorUserId));
    }
    return `/schematics?${params.toString()}`;
}

export function useSchematics(filters: SchematicFilters = {}) {
    const { data, loading, error, refresh } = useApiGet<
        SchematicSummaryType[]
    >(schematicsUrl(filters), "Erreur lors du chargement des schematics");
    return { schematics: data ?? [], loading, error, refresh };
}

export function useSchematic(schematicId: string | undefined) {
    const { data, loading, error, refresh } = useApiGet<SchematicType>(
        schematicId ? `/schematics/${schematicId}` : null,
        "Erreur lors du chargement du schematic",
    );
    return { schematic: data, loading, error, refresh };
}

/** The tags in use, the most used first. */
export function useSchematicTags() {
    const { data, refresh } = useApiGet<TagCountType[]>(
        "/schematics/tags",
        "Erreur lors du chargement des tags",
    );
    return { tags: data ?? [], refresh };
}

/**
 * An object URL for a file the API only gives to logged-in users (an <img>
 * cannot send the Authorization header). `url` null: nothing is loaded.
 * `version` changes force a reload (a replaced preview keeps its URL).
 */
export function useAuthorizedImage(url: string | null, version = "") {
    const [result, setResult] = useState<{ key: string; src: string } | null>(
        null,
    );
    const key = url ? `${url}#${version}` : null;

    useEffect(() => {
        if (!url || !key) return;
        let objectUrl: string | null = null;
        let cancelled = false;
        axios
            .get<Blob>(url, { responseType: "blob" })
            .then((res) => {
                if (cancelled) return;
                objectUrl = URL.createObjectURL(res.data);
                setResult({ key, src: objectUrl });
            })
            .catch(() => {
                if (!cancelled) setResult(null);
            });
        return () => {
            cancelled = true;
            if (objectUrl) URL.revokeObjectURL(objectUrl);
        };
    }, [url, key]);

    return result !== null && result.key === key ? result.src : null;
}
