export type SortDirection = "asc" | "desc";

export type SortOption<K extends string> = { value: K; label: string };

/** Short text for the "Ordre" button, e.g. "Prix ↑" (undefined when not sorted). */
export function sortSummary<K extends string>(
    options: SortOption<K>[],
    value: K | null,
    direction: SortDirection,
): string | undefined {
    const option = options.find((o) => o.value === value);
    if (!option) return undefined;
    return `${option.label} ${direction === "asc" ? "↑" : "↓"}`;
}
