import { useState, useMemo } from "react";
import { NewFaction } from "./buttons/newfaction";
import { useFactions } from "./hooks/factions";
import { useMemberCounts } from "./hooks/member_counts";
import { useMe } from "./hooks/me";
import FactionTable from "./snippets/factions_table";
import ToolbarPanels from "./snippets/toolbar_panels";
import { useFaction } from "./hooks/faction";

type Props = {
    search: string;
    setSearch: (val: string) => void;
    sortKey: string;
    setSortKey: (key: string) => void;
    sortAsc: boolean;
    setSortAsc: (val: boolean) => void;
};

const SORT_LABELS: Record<string, string> = {
    name: "Nom",
    members: "Membres",
    approved: "Validation",
};

function FactionToolbar({
    search,
    setSearch,
    sortKey,
    setSortKey,
    sortAsc,
    setSortAsc,
}: Props) {
    return (
        <ToolbarPanels
            sortSummary={`${SORT_LABELS[sortKey]} ${sortAsc ? "↑" : "↓"}`}
            search={
                <input
                    type="text"
                    placeholder="Rechercher une faction..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            }
            sort={
                <>
                    <select
                        aria-label="Trier par"
                        value={sortKey}
                        onChange={(e) => setSortKey(e.target.value)}
                    >
                        <option value="name">Nom</option>
                        <option value="members">Membres</option>
                        <option value="approved">Validation</option>
                    </select>
                    <button
                        type="button"
                        className={`button sort-direction${sortAsc ? "" : " desc"}`}
                        aria-label={`Ordre ${sortAsc ? "croissant" : "décroissant"}, cliquer pour inverser`}
                        onClick={() => setSortAsc(!sortAsc)}
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
                        {sortAsc ? "Croissant" : "Décroissant"}
                    </button>
                </>
            }
        />
    );
}

export default function FactionList() {
    const { factions, loading, error, refresh } = useFactions();
    const { user } = useMe();
    const { faction: UserFaction } = useFaction(
        user?.faction_id?.toString() ?? null,
    );

    const [search, setSearch] = useState("");
    const [sortKey, setSortKey] = useState("name");
    const [sortAsc, setSortAsc] = useState(true);
    const [page, setPage] = useState(1);
    const pageSize = 10;

    const { counts: memberCounts, refresh: refreshCounts } = useMemberCounts();

    const filteredFactions = useMemo(() => {
        if (!factions) return [];

        return factions
            .filter((f) =>
                [f.name, f.description]
                    .join(" ")
                    .toLowerCase()
                    .includes(search.toLowerCase()),
            )
            .sort((a, b) => {
                let comp = 0;

                if (sortKey === "name") {
                    comp = a.name.localeCompare(b.name);
                } else if (sortKey === "members") {
                    comp =
                        (memberCounts[a.faction_id] ?? 0) -
                        (memberCounts[b.faction_id] ?? 0);
                } else if (sortKey === "approved") {
                    comp =
                        a.is_approved === b.is_approved
                            ? 0
                            : a.is_approved
                              ? -1
                              : 1;
                }

                return sortAsc ? comp : -comp;
            });
    }, [factions, search, sortKey, sortAsc, memberCounts]);

    const totalPages = Math.ceil(filteredFactions.length / pageSize);
    // The list can shrink under the current page (search, new data).
    const currentPage = Math.min(page, Math.max(totalPages, 1));

    const paginated = useMemo(() => {
        const start = (currentPage - 1) * pageSize;
        return filteredFactions.slice(start, start + pageSize);
    }, [filteredFactions, currentPage]);

    return (
        <div className="snippet-container factions-container">
            <div className="factions-header">
                <h2>Liste des factions</h2>
                {(!UserFaction || UserFaction?.name === "Sans Faction") && (
                    <NewFaction
                        onCreated={() => {
                            refresh();
                            refreshCounts();
                        }}
                    />
                )}
            </div>

            <FactionToolbar
                search={search}
                setSearch={(value) => {
                    setSearch(value);
                    setPage(1);
                }}
                sortKey={sortKey}
                setSortKey={setSortKey}
                sortAsc={sortAsc}
                setSortAsc={setSortAsc}
            />

            <FactionTable
                factions={paginated}
                memberCounts={memberCounts}
                onJoined={refreshCounts}
                loading={loading}
                error={error}
                totalPages={totalPages}
                page={currentPage}
                setPage={setPage}
                onRetry={refresh}
            />
        </div>
    );
}
