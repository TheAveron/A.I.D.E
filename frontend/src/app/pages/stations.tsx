import { useState } from "react";
import { Link } from "react-router";

import { useStations } from "../components/hooks/stations";
import { usePagination } from "../components/hooks/pagination";
import NewStation from "../components/snippets/new_station";
import { Pagination } from "../components/snippets/pagination";
import { DIMENSIONS } from "../types/trains";

const PER_PAGE = 20;

/** The index of stations, with their coordinates. */
export default function StationsPage() {
    const [search, setSearch] = useState("");
    const [dimension, setDimension] = useState("");
    const { stations, loading, error } = useStations(search, dimension);
    const { pageItems, page, totalPages, setPage } = usePagination(
        stations,
        PER_PAGE,
    );

    return (
        <div className="information-container">
            <div className="snippet-container">
                <div className="offers-header">
                    <h2>Gares</h2>
                    <Link className="button" to="/lines">
                        Lignes
                    </Link>
                    <Link className="button" to="/trains">
                        Trains
                    </Link>
                </div>
                <div className="toolbar">
                    <input
                        type="text"
                        placeholder="Rechercher une gare..."
                        aria-label="Rechercher une gare"
                        maxLength={60}
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                    <select
                        aria-label="Filtrer par dimension"
                        value={dimension}
                        onChange={(e) => setDimension(e.target.value)}
                    >
                        <option value="">Toutes les dimensions</option>
                        {Object.entries(DIMENSIONS).map(([value, label]) => (
                            <option key={value} value={value}>
                                {label}
                            </option>
                        ))}
                    </select>
                </div>
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Gare</th>
                                <th>Dimension</th>
                                <th>X</th>
                                <th>Y</th>
                                <th>Z</th>
                                <th>Quais</th>
                            </tr>
                        </thead>
                        <tbody>
                            {error ? (
                                <tr>
                                    <td colSpan={6}>{error}</td>
                                </tr>
                            ) : loading ? (
                                <tr>
                                    <td colSpan={6}>Chargement...</td>
                                </tr>
                            ) : pageItems.length === 0 ? (
                                <tr className="empty-state">
                                    <td colSpan={6}>Aucune gare trouvée.</td>
                                </tr>
                            ) : (
                                pageItems.map((station) => (
                                    <tr key={station.station_id}>
                                        <td>
                                            <Link
                                                to={`/station/${station.station_id}`}
                                            >
                                                {station.name}
                                            </Link>
                                        </td>
                                        <td>{DIMENSIONS[station.dimension]}</td>
                                        <td>{station.x}</td>
                                        <td>{station.y ?? "-"}</td>
                                        <td>{station.z}</td>
                                        <td>{station.platforms.length}</td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
                <Pagination
                    page={page}
                    totalPages={totalPages}
                    setPage={setPage}
                />
            </div>
            <NewStation />
        </div>
    );
}
