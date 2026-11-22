import axios from "axios";
import { Fragment, useState, type FormEvent } from "react";
import { Link } from "react-router";

import { UserState } from "./admin_state";
import ToolbarPanels from "../network/toolbar_panels";
import { ADMIN_PAGE, useAdminUsers } from "../../hooks/admin/admin";
import { getErrorMessage } from "../../utils/apierror";
import { GLOBAL_ROLES, GLOBAL_ROLE_LABELS } from "../../utils/audit";
import type { AdminUserType } from "../../types/admin";
import { LEADER_ROLE } from "../../utils/roles";

const PASSWORD_MIN = 4;
const PASSWORD_MAX = 40;

function PasswordReset({
    user,
    onDone,
}: {
    user: AdminUserType;
    onDone: (message: string) => void;
}) {
    const [value, setValue] = useState("");
    const [open, setOpen] = useState(false);
    const [busy, setBusy] = useState(false);

    const submit = async (event: FormEvent) => {
        event.preventDefault();
        if (value.length < PASSWORD_MIN || value.length > PASSWORD_MAX) {
            onDone(
                `❌ Le mot de passe doit faire entre ${PASSWORD_MIN} et ${PASSWORD_MAX} caractères`,
            );
            return;
        }
        setBusy(true);
        try {
            await axios.post(`/admin/users/${user.user_id}/password`, {
                new_password: value,
            });
            onDone(
                `✅ Mot de passe de ${user.username} réinitialisé : transmettez-le lui, il sera invité à le changer`,
            );
            setValue("");
            setOpen(false);
        } catch (err) {
            onDone(`❌ ${getErrorMessage(err)}`);
        } finally {
            setBusy(false);
        }
    };

    if (!open) {
        return (
            <button
                type="button"
                className="button"
                onClick={() => setOpen(true)}
            >
                Mot de passe
            </button>
        );
    }
    return (
        <form onSubmit={submit}>
            <input
                type="password"
                autoComplete="new-password"
                aria-label={`Nouveau mot de passe de ${user.username}`}
                value={value}
                onChange={(e) => setValue(e.target.value)}
            />{" "}
            <button type="submit" className="button" disabled={busy}>
                Valider
            </button>{" "}
            <button
                type="button"
                className="button"
                onClick={() => setOpen(false)}
            >
                Annuler
            </button>
        </form>
    );
}

/** Accounts: search, global roles, faction removal, password reset. */
export default function AdminUsers() {
    const [search, setSearch] = useState("");
    const [role, setRole] = useState("");
    const [page, setPage] = useState(1);
    const [message, setMessage] = useState("");
    const [detailsOf, setDetailsOf] = useState<number | null>(null);
    const { users, loading, error, refresh } = useAdminUsers(
        search,
        role,
        page,
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

    const toggleRole = (user: AdminUserType, name: string) => {
        const has = user.global_roles.includes(name);
        const label = GLOBAL_ROLE_LABELS[name] ?? name;
        if (
            !window.confirm(
                `${has ? "Retirer" : "Donner"} le rôle « ${label} » à ${user.username} ?`,
            )
        ) {
            return;
        }
        return run(
            () =>
                has
                    ? axios.delete(`/global-roles/${user.user_id}/${name}`)
                    : axios.put(`/global-roles/${user.user_id}/${name}`),
            `✅ Rôle « ${label} » ${has ? "retiré à" : "donné à"} ${user.username}`,
        );
    };

    const detach = (user: AdminUserType) => {
        if (
            !window.confirm(
                `Retirer ${user.username} de la faction ${user.faction_name} ?`,
            )
        ) {
            return;
        }
        return run(
            () => axios.post(`/admin/users/${user.user_id}/detach`),
            `✅ ${user.username} n'a plus de faction`,
        );
    };

    return (
        <div className="snippet-container">
            <h2>Comptes</h2>
            <ToolbarPanels
                activeFilters={role ? 1 : 0}
                search={
                    <input
                        type="text"
                        placeholder="Nom ou email..."
                        aria-label="Rechercher un compte"
                        maxLength={60}
                        value={search}
                        onChange={(e) => {
                            setSearch(e.target.value);
                            setPage(1);
                        }}
                    />
                }
                filters={
                    <select
                        aria-label="Filtrer par rôle global"
                        value={role}
                        onChange={(e) => {
                            setRole(e.target.value);
                            setPage(1);
                        }}
                    >
                        <option value="">Tous les comptes</option>
                        {GLOBAL_ROLES.map((r) => (
                            <option key={r} value={r}>
                                {GLOBAL_ROLE_LABELS[r]}
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
                            <th>Compte</th>
                            <th>Email</th>
                            <th>Faction</th>
                            <th>Rôles globaux</th>
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
                        ) : users.length === 0 ? (
                            <tr className="empty-state">
                                <td colSpan={5}>Aucun compte trouvé.</td>
                            </tr>
                        ) : (
                            users.map((u) => (
                                <Fragment key={u.user_id}>
                                    <tr>
                                        <td>
                                            <Link to={`/user/${u.user_id}`}>
                                                {u.username}
                                            </Link>
                                        </td>
                                        <td>{u.email ?? "-"}</td>
                                        <td>
                                            {u.faction_name ?? "-"}
                                            {u.role_name && (
                                                <small> ({u.role_name})</small>
                                            )}
                                        </td>
                                        <td>
                                            {GLOBAL_ROLES.map((r) => (
                                                <label key={r}>
                                                    <input
                                                        type="checkbox"
                                                        checked={u.global_roles.includes(
                                                            r,
                                                        )}
                                                        onChange={() =>
                                                            toggleRole(u, r)
                                                        }
                                                    />{" "}
                                                    {GLOBAL_ROLE_LABELS[r]}{" "}
                                                </label>
                                            ))}
                                        </td>
                                        <td>
                                            <button
                                                type="button"
                                                className="button"
                                                aria-expanded={
                                                    detailsOf === u.user_id
                                                }
                                                onClick={() =>
                                                    setDetailsOf(
                                                        detailsOf === u.user_id
                                                            ? null
                                                            : u.user_id,
                                                    )
                                                }
                                            >
                                                État
                                            </button>{" "}
                                            <PasswordReset
                                                user={u}
                                                onDone={setMessage}
                                            />{" "}
                                            {/* A leader hands over first (409) */}
                                            {u.faction_name &&
                                                u.faction_name !==
                                                    "Sans Faction" &&
                                                u.role_name !== LEADER_ROLE && (
                                                    <button
                                                        type="button"
                                                        className="button"
                                                        onClick={() =>
                                                            detach(u)
                                                        }
                                                    >
                                                        Retirer de la faction
                                                    </button>
                                                )}
                                        </td>
                                    </tr>
                                    {detailsOf === u.user_id && (
                                        <tr>
                                            <td colSpan={5}>
                                                <UserState userId={u.user_id} />
                                            </td>
                                        </tr>
                                    )}
                                </Fragment>
                            ))
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
                    disabled={users.length < ADMIN_PAGE}
                    onClick={() => setPage(page + 1)}
                >
                    Suivant
                </button>
            </div>
        </div>
    );
}
