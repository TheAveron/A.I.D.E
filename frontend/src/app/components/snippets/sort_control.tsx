import type { SortDirection, SortOption } from "./sort_utils";

/**
 * The sort controls of every list: a criterion picker and a button that flips
 * the direction. Meant to be used as the `sort` panel of <ToolbarPanels>.
 */
export default function SortControl<K extends string>({
    options,
    value,
    direction,
    onChange,
    noneLabel,
    defaultDirection,
}: {
    options: SortOption<K>[];
    // Current criterion, or null when the list is not sorted
    value: K | null;
    direction: SortDirection;
    onChange: (value: K | null, direction: SortDirection) => void;
    // When set, adds an entry that turns the sort off
    noneLabel?: string;
    // Direction used when a criterion is picked (defaults to the current one)
    defaultDirection?: (value: K) => SortDirection;
}) {
    const ascending = direction === "asc";

    return (
        <>
            <select
                aria-label="Trier par"
                value={value ?? ""}
                onChange={(e) => {
                    const next = e.target.value as K | "";
                    if (next === "") {
                        onChange(null, direction);
                    } else {
                        onChange(next, defaultDirection?.(next) ?? direction);
                    }
                }}
            >
                {noneLabel && <option value="">{noneLabel}</option>}
                {options.map((option) => (
                    <option key={option.value} value={option.value}>
                        {option.label}
                    </option>
                ))}
            </select>
            <button
                type="button"
                className={`button sort-direction${ascending ? "" : " desc"}`}
                disabled={value === null}
                aria-label={`Ordre ${ascending ? "croissant" : "décroissant"}, cliquer pour inverser`}
                onClick={() => onChange(value, ascending ? "desc" : "asc")}
            >
                <svg
                    viewBox="0 0 24 24"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                >
                    <path d="M12 19V5" />
                    <path d="m5 12 7-7 7 7" />
                </svg>
                {ascending ? "Croissant" : "Décroissant"}
            </button>
        </>
    );
}
