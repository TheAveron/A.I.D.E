import type { UserType } from "../types/users";
import { Link } from "react-router-dom";
import { useRole } from "./hooks/role";
import { useFaction } from "./hooks/faction";

import "../../assets/css/components/info.css";
import "../../assets/css/components/snippets.css";

function Profile({ value }: { value: UserType }) {
    const profile = value;

    const factionId = profile.faction_id?.toString() ?? "";
    const roleId = profile.role_id?.toString() ?? "";

    const { faction, loading: factionLoading } = useFaction(factionId);
    const { role, loading: roleLoading } = useRole(roleId);

    if (
        (profile.faction_id && factionLoading) ||
        (profile.role_id && roleLoading)
    ) {
        return <p>Chargement...</p>;
    }

    return (
        <div className="snippet-container">
            <div className="info-header">
                <div className="info-title">{profile.username}</div>
                {profile.is_admin && (
                    <div className="profile-role">Administrateur</div>
                )}
            </div>

            <div className="info-values">
                <Link
                    to={
                        faction ? `/A.I.D.E/faction/${faction.faction_id}` : "#"
                    }
                    style={{ width: "100%" }}
                >
                    <div className="info-row">
                        <span className="info-label">Faction:</span>
                        <span className="info-value-field">
                            {faction?.name ?? "Aucune"}
                        </span>
                    </div>
                </Link>
                <div className="info-row">
                    <span className="info-label">Role:</span>
                    <span className="info-value-field">
                        {role?.name ?? "Aucun"}
                    </span>
                </div>
                <div className="info-row">
                    <span className="info-label">Email:</span>
                    <span className="info-value-field">
                        {profile.email ?? "Non"}
                    </span>
                </div>
                <div className="info-row">
                    <span className="info-label">Inscription:</span>
                    <span className="info-value-field">
                        {new Date(profile.created_at).toLocaleDateString()}
                    </span>
                </div>
            </div>
        </div>
    );
}

export default Profile;
