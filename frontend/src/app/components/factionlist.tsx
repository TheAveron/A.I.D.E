import { useState, useMemo } from "react";
import { NewFaction } from "./buttons/newfaction";
import { useFactions } from "./hooks/factions";
import { useAllMemberCounts } from "./snippets/member_count";
import { useMe } from "./hooks/me";

import FactionTable from "./snippets/factions_table";

type Props = {
    search: string;
    setSearch: (val: string) => void;
    sortKey: string;
    setSortKey: (key: string) => void;
    sortAsc: boolean;
    setSortAsc: (val: boolean) => void;
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
        <div className="toolbar">
            <input
                type="text"
                placeholder="Rechercher une faction..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
            />
            <select
                value={sortKey}
                onChange={(e) => setSortKey(e.target.value)}
            >
                <option value="name">Nom</option>
                <option value="members">Membres</option>
                <option value="approved">Validation</option>
            </select>
            <div className="button" onClick={() => setSortAsc(!sortAsc)}>
                {sortAsc ? "⬆️" : "⬇️"}
            </div>
        </div>
    );
}

export default function FactionList() {
    const { factions, loading, error } = useFactions();
    const { user } = useMe();

    const [search, setSearch] = useState("");
    const [sortKey, setSortKey] = useState("name");
    const [sortAsc, setSortAsc] = useState(true);
    const [page, setPage] = useState(1);
    const pageSize = 10;

    const { counts: memberCounts } = useAllMemberCounts(factions);

    const filteredFactions = useMemo(() => {
        if (!factions) return [];

        return factions
            .filter((f) =>
                [f.name, f.description]
                    .join(" ")
                    .toLowerCase()
                    .includes(search.toLowerCase())
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

    const paginated = useMemo(() => {
        const start = (page - 1) * pageSize;
        return filteredFactions.slice(start, start + pageSize);
    }, [filteredFactions, page]);

    const totalPages = Math.ceil(filteredFactions.length / pageSize);

    return (
        <div className="snippet-container factions-container">
            <div className="factions-header">
                <h2>Liste des factions</h2>
                {!user?.faction_id && <NewFaction />}
            </div>

            <FactionToolbar
                search={search}
                setSearch={setSearch}
                sortKey={sortKey}
                setSortKey={setSortKey}
                sortAsc={sortAsc}
                setSortAsc={setSortAsc}
            />

            <FactionTable
                factions={paginated}
                loading={loading}
                error={error}
                totalPages={totalPages}
                page={page}
                setPage={setPage}
            />
        </div>
    );
}
