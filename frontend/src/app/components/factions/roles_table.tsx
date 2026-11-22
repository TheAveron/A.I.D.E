import axios from "axios";
import { useState } from "react";
import { useParams } from "react-router";

import { getErrorMessage } from "../../utils/apierror";
import { type RoleType } from "../../types/roles";
import { useMe } from "../../hooks/users/me";
import { useRole } from "../../hooks/factions/role";
import { useRoles } from "../../hooks/factions/factionroles";
import RoleEditor from "./role_editor";
import { isGuestRole, isLeaderRole } from "../../utils/roles";

function RolesList({
    roles,
    canManage,
    ownRoleId,
    onEdit,
    onDelete,
}: {
    roles: RoleType[] | null;
    canManage: boolean;
    ownRoleId: number | null;
    onEdit: (role: RoleType) => void;
    onDelete: (role: RoleType) => void;
}) {
    if (!roles) {
        return (
            <tr>
                <td colSpan={12}>Aucun rôle trouvé.</td>
            </tr>
        );
    }

    const sortedRoles = [...roles].sort((a, b) => {
        const countPermissions = (role: RoleType) =>
            [
                role.accept_offers,
                role.create_offers,
                role.manage_funds,
                role.handle_members,
                role.manage_roles,
                role.manage_docs,
                role.manage_trains,
                role.manage_territory,
                role.view_transactions,
            ].filter(Boolean).length;
        return countPermissions(a) - countPermissions(b);
    });

    return sortedRoles.map((role) => (
        <tr key={role.role_id}>
            <td>{role.name}</td>
            <td>{role.description}</td>
            <td>{role.view_transactions ? "✅" : "❌"}</td>
            <td>{role.accept_offers ? "✅" : "❌"}</td>
            <td>{role.create_offers ? "✅" : "❌"}</td>
            <td>{role.manage_funds ? "✅" : "❌"}</td>
            <td>{role.manage_docs ? "✅" : "❌"}</td>
            <td>{role.manage_trains ? "✅" : "❌"}</td>
            <td>{role.manage_territory ? "✅" : "❌"}</td>
            <td>{role.handle_members ? "✅" : "❌"}</td>
            <td>{role.manage_roles ? "✅" : "❌"}</td>
            {canManage && (
                <td>
                    {!isLeaderRole(role) && role.role_id !== ownRoleId && (
                        <>
                            <button
                                type="button"
                                className="button"
                                onClick={() => onEdit(role)}
                            >
                                Modifier
                            </button>
                            {/* Joining relies on it: the server keeps it */}
                            {!isGuestRole(role) && (
                                <>
                                    {" "}
                                    <button
                                        type="button"
                                        className="button"
                                        onClick={() => onDelete(role)}
                                    >
                                        Supprimer
                                    </button>
                                </>
                            )}
                        </>
                    )}
                </td>
            )}
        </tr>
    ));
}

export default function RolesTable() {
    const { factionid } = useParams();
    const { roles, loading, error, refresh } = useRoles(factionid ?? null);
    const { user } = useMe();
    const { role: ownRole } = useRole(user?.role_id ?? null);
    // Same rule as the API: managing the roles of one's own faction
    const canManage =
        !!ownRole?.manage_roles &&
        ownRole.faction_id === Number(factionid) &&
        user?.faction_id === Number(factionid);
    // null: nothing open, "new": creating, a role: editing it
    const [editing, setEditing] = useState<RoleType | "new" | null>(null);
    const [actionError, setActionError] = useState("");

    const remove = async (role: RoleType) => {
        if (!window.confirm(`Supprimer le rôle « ${role.name} » ?`)) return;
        setActionError("");
        try {
            await axios.delete(`/roles/delete/${role.role_id}`);
            refresh();
        } catch (err) {
            setActionError(getErrorMessage(err));
        }
    };

    if (!factionid) {
        return <p>Faction introuvable.</p>;
    }

    if (loading) return <p>Chargement des rôles...</p>;
    if (error) return <p role="alert">{error}</p>;

    return (
        <div className="snippet-container roles-container">
            <h2>Rôles</h2>
            {canManage && !editing && (
                <button
                    type="button"
                    className="button"
                    onClick={() => setEditing("new")}
                >
                    Nouveau rôle
                </button>
            )}
            {actionError && <p role="alert">{actionError}</p>}
            {canManage && editing && ownRole && (
                <RoleEditor
                    key={editing === "new" ? "new" : editing.role_id}
                    factionId={Number(factionid)}
                    role={editing === "new" ? null : editing}
                    actorRole={ownRole}
                    onDone={(changed) => {
                        setEditing(null);
                        if (changed) refresh();
                    }}
                />
            )}
            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Nom</th>
                            <th>Description</th>
                            <th>Voir les Transactions</th>
                            <th>Accepter les Offres</th>
                            <th>Créer des Offres</th>
                            <th>Gérer la Monnaie</th>
                            <th>Gérer les Documents</th>
                            <th>Gérer les Trains</th>
                            <th>Gérer la Carte</th>
                            <th>Gérer les Membres</th>
                            <th>Gérer les Rôles</th>
                            {canManage && <th>Action</th>}
                        </tr>
                    </thead>
                    <tbody>
                        <RolesList
                            roles={roles}
                            canManage={canManage}
                            ownRoleId={user?.role_id ?? null}
                            onEdit={setEditing}
                            onDelete={remove}
                        />
                    </tbody>
                </table>
            </div>
        </div>
    );
}
