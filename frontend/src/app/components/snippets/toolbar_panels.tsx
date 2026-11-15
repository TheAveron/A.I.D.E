import { useId, useState, type ReactNode } from "react";

/**
 * The toolbar of a list: the search field stays visible, the filters and the
 * sort controls hide behind two buttons that open their own panel.
 */
export default function ToolbarPanels({
    search,
    filters,
    sort,
    activeFilters = 0,
    sortSummary,
}: {
    // Always visible (usually the text search)
    search?: ReactNode;
    // Content of the "Filtres" panel; the button is hidden when absent
    filters?: ReactNode;
    // Content of the "Ordre" panel; the button is hidden when absent
    sort?: ReactNode;
    // How many filters are set, shown on the button
    activeFilters?: number;
    // Current sort (e.g. "Prix ↑"), shown on the button
    sortSummary?: string;
}) {
    const baseId = useId();
    const [filtersOpen, setFiltersOpen] = useState(false);
    const [sortOpen, setSortOpen] = useState(false);

    const filtersId = `${baseId}-filters`;
    const sortId = `${baseId}-sort`;

    return (
        <div className="toolbar-panels">
            <div className="toolbar">
                {search}
                {filters && (
                    <button
                        type="button"
                        className="button toolbar-toggle"
                        aria-expanded={filtersOpen}
                        aria-controls={filtersId}
                        onClick={() => setFiltersOpen((open) => !open)}
                    >
                        Filtres
                        {activeFilters > 0 && (
                            <span
                                className="toolbar-badge"
                                aria-label={`${activeFilters} filtre(s) actif(s)`}
                            >
                                {activeFilters}
                            </span>
                        )}
                    </button>
                )}
                {sort && (
                    <button
                        type="button"
                        className="button toolbar-toggle"
                        aria-expanded={sortOpen}
                        aria-controls={sortId}
                        onClick={() => setSortOpen((open) => !open)}
                    >
                        Ordre
                        {sortSummary && (
                            <span className="toolbar-summary">
                                {sortSummary}
                            </span>
                        )}
                    </button>
                )}
            </div>
            {filters && (
                <div
                    id={filtersId}
                    className="toolbar toolbar-panel"
                    hidden={!filtersOpen}
                >
                    {filters}
                </div>
            )}
            {sort && (
                <div
                    id={sortId}
                    className="toolbar toolbar-panel"
                    hidden={!sortOpen}
                >
                    {sort}
                </div>
            )}
        </div>
    );
}
