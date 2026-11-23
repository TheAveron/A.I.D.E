import { useState } from "react";
import { Link } from "react-router";

import { useLines, useTrains } from "../../hooks/network/trains";
import { useMe } from "../../hooks/users/me";
import { usePagination } from "../../hooks/common/pagination";
import { Pagination } from "../../components/common/pagination";
import ToolbarPanels from "../../components/network/toolbar_panels";
import TrainOwner from "../../components/network/train_owner";
import { SERVICE_NAMES } from "../../utils/trains";
import type { TrainService } from "../../types/trains";
import PageHeader from "../../components/common/page_header";

const PER_PAGE = 20;

/** The index of trains, with filters by line, service, owner and name. */
export default function TrainsPage() {
    const { user } = useMe();
    const { lines } = useLines();

    const [line, setLine] = useState("");
    const [service, setService] = useState("");
    const [search, setSearch] = useState("");
    const [mine, setMine] = useState(false);
    const [retired, setRetired] = useState(false);

    const { trains, loading, error } = useTrains({
        line,
        service,
        q: search,
        includeRetired: retired,
        ownerUserId: mine ? (user?.user_id ?? null) : null,
    });
    const { pageItems, page, totalPages, setPage } = usePagination(
        trains,
        PER_PAGE,
    );

    return (
        <div className="information-container">
            <PageHeader
                title="Trains"
                description="Le registre des trains en circulation : leur ligne, leur service et leur propriétaire."
                actions={
                    <Link className="button" to="/trains/new">
                        Enregistrer un train
                    </Link>
                }
            />
            <div className="snippet-container">

                <ToolbarPanels
                    activeFilters={
                        [line, service, mine, retired].filter(Boolean).length
                    }
                    search={
                        <input
                            type="text"
                            placeholder="Nom ou ancien nom..."
                            aria-label="Rechercher un train"
                            maxLength={50}
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    }
                    filters={
                        <>
                            <select
                                aria-label="Filtrer par ligne"
                                value={line}
                                onChange={(e) => setLine(e.target.value)}
                            >
                                <option value="">Toutes les lignes</option>
                                {lines.map((l) => (
                                    <option key={l.code} value={l.code}>
                                        {l.code}
                                        {l.name ? ` - ${l.name}` : ""}
                                    </option>
                                ))}
                            </select>
                            <select
                                aria-label="Filtrer par service"
                                value={service}
                                onChange={(e) => setService(e.target.value)}
                            >
                                <option value="">Tous les services</option>
                                {(
                                    Object.keys(SERVICE_NAMES) as TrainService[]
                                ).map((s) => (
                                    <option key={s} value={s}>
                                        {s} - {SERVICE_NAMES[s]}
                                    </option>
                                ))}
                            </select>
                            <label>
                                <input
                                    type="checkbox"
                                    checked={mine}
                                    onChange={(e) => setMine(e.target.checked)}
                                />{" "}
                                Mes trains
                            </label>
                            <label>
                                <input
                                    type="checkbox"
                                    checked={retired}
                                    onChange={(e) =>
                                        setRetired(e.target.checked)
                                    }
                                />{" "}
                                Avec les trains retirés
                            </label>
                        </>
                    }
                />

                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Nom</th>
                                <th>Service</th>
                                <th>Ancien nom</th>
                                <th>Propriétaire</th>
                                <th>État</th>
                            </tr>
                        </thead>
                        <tbody>
                            {error ? (
                                <tr>
                                    <td colSpan={5}>{error}</td>
                                </tr>
                            ) : loading ? (
                                <tr>
                                    <td colSpan={5}>Chargement...</td>
                                </tr>
                            ) : pageItems.length === 0 ? (
                                <tr className="empty-state">
                                    <td colSpan={5}>Aucun train trouvé.</td>
                                </tr>
                            ) : (
                                pageItems.map((train) => (
                                    <tr key={train.train_id}>
                                        <td
                                            className={
                                                train.retired_at
                                                    ? "train-retired"
                                                    : undefined
                                            }
                                        >
                                            <Link
                                                to={`/train/${train.train_id}`}
                                            >
                                                {train.display_name}
                                            </Link>
                                        </td>
                                        <td>
                                            {train.service
                                                ? SERVICE_NAMES[train.service]
                                                : "Entretien"}
                                        </td>
                                        <td>{train.legacy_id ?? "-"}</td>
                                        <td>
                                            <TrainOwner train={train} />
                                        </td>
                                        <td>
                                            {train.retired_at
                                                ? "Retiré"
                                                : "En service"}
                                        </td>
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
        </div>
    );
}
