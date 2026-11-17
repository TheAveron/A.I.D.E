import axios from "axios";
import { Fragment, useState } from "react";
import { Link } from "react-router";

import { FactionState as FactionStatePanel } from "./admin_state";
import ToolbarPanels from "../network/toolbar_panels";
import { useAdminFactions } from "../../hooks/admin/admin";
import { getErrorMessage } from "../../utils/apierror";
import type { AdminFactionType, FactionState } from "../../types/admin";

const STATES: [FactionState, string][] = [
    ["all", "Toutes"],
    ["pending", "En attente d'approbation"],
    ["approved", "Approuvées"],
    ["archived", "Archivées"],
];

/** Every faction: approve them, review the archived ones, delete a faction. */
export default function AdminFactions() {
    const [state, setState] = useState<FactionState>("pending");
    const [search, setSearch] = useState("");
    const [message, setMessage] = useState("");
    const [detailsOf, setDetailsOf] = useState<number | null>(null);
    const { factions, loading, error, refresh } = useAdminFactions(
        state,
        search,
    );

    const run = async (action: () => Promise<unknown>, done: string) => {
        setMessage("");
        try {
            await action();
            setMessage(done);
            refresh();
        } catch (err) {
            setMessage(`❌ ${getErrorMessage(err)}`);
        }
    };

    const setApproved = (f: AdminFactionType, value: boolean) =>
        run(
            () =>
                axios.put(`/factions/update/${f.faction_id}`, {
                    is_approved: value,
                }),
            `✅ ${f.name} ${value ? "approuvée" : "n'est plus approuvée"}`,
        );

    const remove = (f: AdminFactionType) => {
        if (
            !window.confirm(
                `Supprimer (archiver) la faction ${f.name} ? Ses ${f.member_count} membres seront renvoyés sans faction.`,
            )
        ) {
            return;
        }
        return run(
            () => axios.delete(`/factions/delete/${f.faction_id}`),
            `✅ ${f.name} archivée`,
        );
    };

    return (
        <div className="snippet-container">
            <h2>Factions</h2>
            <ToolbarPanels
                activeFilters={state !== STATES[0][0] ? 1 : 0}
                search={
                    <input
                        type="text"
                        placeholder="Rechercher une faction..."
                        aria-label="Rechercher une faction"
                        maxLength={100}
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                }
                filters={
                    <select
                        aria-label="Filtrer par état"
                        value={state}
                        onChange={(e) =>
                            setState(e.target.value as FactionState)
                        }
                    >
                        {STATES.map(([value, label]) => (
                            <option key={value} value={value}>
                                {label}
                            </option>
                        ))}
                    </select>
                }
            />
            {message && <p role="status">{message}</p>}
            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Faction</th>
                            <th>Membres</th>
                            <th>Adhésion</th>
                            <th>État</th>
                            <th>Actions</th>
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
                        ) : factions.length === 0 ? (
                            <tr className="empty-state">
                                <td colSpan={5}>Aucune faction.</td>
                            </tr>
                        ) : (
                            factions.map((f) => (
                                <Fragment key={f.faction_id}>
                                    <tr>
                                        <td>
                                            <Link
                                                to={`/faction/${f.faction_id}`}
                                            >
                                                {f.name}
                                            </Link>
                                        </td>
                                        <td>{f.member_count}</td>
                                        <td>
                                            {f.requires_approval
                                                ? "Sur demande"
                                                : "Libre"}
                                        </td>
                                        <td>
                                            {f.deleted_at
                                                ? `Archivée le ${new Date(f.deleted_at).toLocaleDateString()}`
                                                : f.is_approved
                                                  ? "Approuvée"
                                                  : "En attente"}
                                        </td>
                                        <td>
                                            <button
                                                type="button"
                                                className="button"
                                                aria-expanded={
                                                    detailsOf === f.faction_id
                                                }
                                                onClick={() =>
                                                    setDetailsOf(
                                                        detailsOf ===
                                                            f.faction_id
                                                            ? null
                                                            : f.faction_id,
                                                    )
                                                }
                                            >
                                                État
                                            </button>{" "}
                                            {!f.deleted_at && (
                                                <>
                                                    <button
                                                        type="button"
                                                        className="button"
                                                        onClick={() =>
                                                            setApproved(
                                                                f,
                                                                !f.is_approved,
                                                            )
                                                        }
                                                    >
                                                        {f.is_approved
                                                            ? "Retirer l'approbation"
                                                            : "Approuver"}
                                                    </button>{" "}
                                                    <button
                                                        type="button"
                                                        className="button"
                                                        onClick={() =>
                                                            remove(f)
                                                        }
                                                    >
                                                        Supprimer
                                                    </button>
                                                </>
                                            )}
                                        </td>
                                    </tr>
                                    {detailsOf === f.faction_id && (
                                        <tr>
                                            <td colSpan={5}>
                                                <FactionStatePanel
                                                    factionId={f.faction_id}
                                                />
                                            </td>
                                        </tr>
                                    )}
                                </Fragment>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
