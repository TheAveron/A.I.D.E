import { useParams } from "react-router-dom";
import { type RoleType } from "../../types/roles";
import { useRoles } from "../hooks/factionroles";

function RolesList({ roles }: { roles: RoleType[] | null }) {
    if (!roles) {
        return (
            <tr>
                <td colSpan={8}>Aucun Role trouvé.</td>
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
            <td>{role.handle_members ? "✅" : "❌"}</td>
            <td>{role.manage_roles ? "✅" : "❌"}</td>
        </tr>
    ));
}

export default function RolesTable() {
    const { factionid } = useParams();
    const { roles, loading } = useRoles(factionid ?? null);

    if (!factionid) {
        return <p>No faction id provided</p>;
    }

    if (loading) return <p>Chargement des roles...</p>;

    return (
        <div className="snippet-container roles-container">
            <h2>Roles</h2>
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
                            <th>Gérer les Membres</th>
                            <th>Gérer les Roles</th>
                        </tr>
                    </thead>
                    <tbody>
                        <RolesList roles={roles} />
                    </tbody>
                </table>
            </div>
        </div>
    );
}
