import { useNavigate, useParams } from "react-router-dom";

import { useRole } from "../hooks/role";
import { useMembers } from "../hooks/factionmembers";
import { useMe } from "../hooks/me";
import { UpdateRole } from "../buttons/updaterole";

import type { CSSProperties } from "react";

function RoleElement({
    role_id,
    faction_id,
    user_id,
}: {
    role_id: number | null;
    faction_id: number | null;
    user_id: number;
}) {
    const navigate = useNavigate();
    const { role } = useRole(role_id);

    if (!role_id) {
        return (
            <>
                <td>Pas de rôle renseigné</td>
                <td></td>
            </>
        );
    }

    if (!role) {
        return (
            <>
                <td>No role found with this id</td>
                <td></td>
            </>
        );
    }

    return (
        <>
            <td
                onClick={() => {
                    navigate("/A.I.D.E/user/" + user_id);
                }}
            >
                {role.name}
            </td>
            {role.handle_members &&
                role.faction_id === faction_id &&
                role.name != "Chef" && (
                    <td
                        onClick={(e) => {
                            e.preventDefault(); // prevents navigation
                            e.stopPropagation(); // stops bubbling to Link
                        }}
                    >
                        <UpdateRole
                            userId={user_id}
                            currentRoleId={role_id}
                            factionId={faction_id}
                            onRoleUpdated={() => {
                                window.location.reload();
                            }}
                        />
                    </td>
                )}
        </>
    );
}

function UsersTable({ state = false }: { state: boolean }) {
    const navigate = useNavigate();

    const { factionid } = useParams();
    const { users, loading, error } = useMembers(factionid ?? null);
    const { user: current_user } = useMe();

    const style: CSSProperties = { gridColumn: "2 / span 2" };
    const nostyle: CSSProperties = { gridColumn: "1 / span 2" };

    return (
        <div
            id="user-list"
            className="snippet-container users-container"
            style={state ? nostyle : style}
        >
            <div className="info-header">
                <div className="info-title">Membres</div>
            </div>
            <div className="info-values table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Nom</th>
                            <th colSpan={2}>Role</th>
                        </tr>
                    </thead>
                    <tbody>
                        {!error ? (
                            !loading ? (
                                users && users.length > 0 ? (
                                    users.map((user) => (
                                        <tr key={user.user_id}>
                                            <td
                                                onClick={() => {
                                                    navigate(
                                                        "/A.I.D.E/user/" +
                                                            user.user_id
                                                    );
                                                }}
                                            >
                                                {user.username}
                                            </td>
                                            <RoleElement
                                                user_id={user.user_id}
                                                role_id={user.role_id}
                                                faction_id={
                                                    current_user?.faction_id ??
                                                    null
                                                }
                                            />
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan={5}>
                                            Aucun utilisateur trouvé.
                                        </td>
                                    </tr>
                                )
                            ) : (
                                <tr>
                                    <td colSpan={5}>
                                        Chargement des membres...
                                    </td>
                                </tr>
                            )
                        ) : (
                            <tr>
                                <td colSpan={5}>{error}</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default UsersTable;
