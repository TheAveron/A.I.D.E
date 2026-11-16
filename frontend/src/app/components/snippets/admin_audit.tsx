import { useState } from "react";
import { Link } from "react-router";

import ToolbarPanels from "./toolbar_panels";
import { ADMIN_PAGE, useAuditLog } from "../hooks/admin";
import { AUDIT_LABELS, TARGET_LABELS, targetLink } from "../../utils/audit";

/** The staff audit trail, newest first. */
export default function AdminAudit() {
    const [action, setAction] = useState("");
    const [targetType, setTargetType] = useState("");
    const [page, setPage] = useState(1);
    const { entries, loading, error } = useAuditLog(action, targetType, page);

    return (
        <div className="snippet-container">
            <h2>Journal d&apos;audit</h2>
            <ToolbarPanels
                activeFilters={[action, targetType].filter(Boolean).length}
                filters={
                    <>
                        <select
                            aria-label="Filtrer par action"
                            value={action}
                            onChange={(e) => {
                                setAction(e.target.value);
                                setPage(1);
                            }}
                        >
                            <option value="">Toutes les actions</option>
                            {Object.entries(AUDIT_LABELS).map(
                                ([value, label]) => (
                                    <option key={value} value={value}>
                                        {label}
                                    </option>
                                ),
                            )}
                        </select>
                        <select
                            aria-label="Filtrer par cible"
                            value={targetType}
                            onChange={(e) => {
                                setTargetType(e.target.value);
                                setPage(1);
                            }}
                        >
                            <option value="">Toutes les cibles</option>
                            {Object.entries(TARGET_LABELS).map(
                                ([value, label]) => (
                                    <option key={value} value={value}>
                                        {label}
                                    </option>
                                ),
                            )}
                        </select>
                    </>
                }
            />
            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Par</th>
                            <th>Action</th>
                            <th>Cible</th>
                            <th>Détail</th>
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
                        ) : entries.length === 0 ? (
                            <tr className="empty-state">
                                <td colSpan={5}>Aucune entrée.</td>
                            </tr>
                        ) : (
                            entries.map((e) => {
                                const link = targetLink(
                                    e.target_type,
                                    e.target_id,
                                );
                                return (
                                    <tr key={e.log_id}>
                                        <td>
                                            {new Date(
                                                e.created_at,
                                            ).toLocaleString()}
                                        </td>
                                        <td>{e.actor_name}</td>
                                        <td>
                                            {AUDIT_LABELS[e.action] ?? e.action}
                                        </td>
                                        <td>
                                            {TARGET_LABELS[e.target_type] ??
                                                e.target_type}{" "}
                                            {link ? (
                                                <Link to={link}>
                                                    {e.target_name ??
                                                        `#${e.target_id}`}
                                                </Link>
                                            ) : (
                                                (e.target_name ?? "")
                                            )}
                                        </td>
                                        <td>{e.detail ?? "-"}</td>
                                    </tr>
                                );
                            })
                        )}
                    </tbody>
                </table>
            </div>
            <div className="pagination-controls">
                <button
                    type="button"
                    className="button"
                    disabled={page <= 1}
                    onClick={() => setPage(page - 1)}
                >
                    Précédent
                </button>
                <span>Page {page}</span>
                <button
                    type="button"
                    className="button"
                    disabled={entries.length < ADMIN_PAGE}
                    onClick={() => setPage(page + 1)}
                >
                    Suivant
                </button>
            </div>
        </div>
    );
}
