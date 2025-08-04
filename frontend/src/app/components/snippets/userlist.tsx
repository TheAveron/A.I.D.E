import { useParams } from "react-router-dom";
import { useMembers } from "../hooks/factionmembers";
import { Link } from "react-router-dom";
import { useRole } from "../hooks/role";

import PenImg from "../../../assets/images/penedit.png";

import "../../../assets/css/components/tables.css";
import "../../../assets/css/components/info.css";

function RoleElement({ role_id }: { role_id: string | undefined }) {
    const { role } = useRole(role_id ?? null);

    if (!role_id) {
        return <p>Pas de role renseigné</p>;
    }

    if (!role) {
        return <p>No role found with this id</p>;
    }

    return (
        <>
            <td>{role.name}</td>
            {role.name != "Chef" ? (
                <td>
                    <div className="button">edit</div>
                </td>
            ) : (
                <td></td>
            )}
        </>
    );
}

function UsersTable() {
    const { factionid } = useParams();
    const { users, loading } = useMembers(factionid ?? null);

    if (!factionid) {
        return <p>No faction id provided</p>;
    }

    if (loading) return <p>Chargement des membres...</p>;

    return (
        <div className="snippet-container users-container">
            <div className="info-header">
                <div className="info-title">Membres</div>
            </div>
            <div className="info-values">
                <table>
                    <thead>
                        <tr>
                            <th>Nom</th>
                            <th>Role</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        {users && users.length > 0 ? (
                            users.map((user) => (
                                <Link
                                    style={{ display: "table-row" }}
                                    key={user.user_id}
                                    to={"/A.I.D.E/user/" + user.user_id}
                                >
                                    <td>{user.username}</td>
                                    <RoleElement
                                        role_id={user.role_id?.toString()}
                                    />
                                </Link>
                            ))
                        ) : (
                            <tr>
                                <td colSpan={5}>Aucun utilisateur trouvé.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default UsersTable;
