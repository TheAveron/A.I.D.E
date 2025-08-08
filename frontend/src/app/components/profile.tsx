import type { UserType } from "../types/users";
import { Link } from "react-router-dom";
import { useRole } from "./hooks/role";
import { useFaction } from "./hooks/faction";

function Profile({ value }: { value: UserType }) {
    const profile = value;

    const factionId = profile.faction_id?.toString() ?? null;
    const roleId = profile.role_id ?? null;

    const {
        faction,
        loading: factionLoading,
        error: factionError,
    } = useFaction(factionId);
    const { role, loading: roleLoading, error: roleError } = useRole(roleId);

    return (
        <div className="snippet-container user-container">
            {!factionError ? (
                !factionLoading ? (
                    <>
                        <div
                            className="info-header"
                            style={
                                profile.is_admin
                                    ? {
                                          justifyContent: "space-between",
                                      }
                                    : {}
                            }
                        >
                            <div className="info-title">{profile.username}</div>
                            {profile.is_admin && (
                                <div className="profile-role">
                                    Administrateur
                                </div>
                            )}
                        </div>
                        <div className="info-values">
                            <Link
                                to={
                                    faction
                                        ? `/A.I.D.E/faction/${faction.faction_id}`
                                        : "#"
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
                                    {!roleError
                                        ? !roleLoading
                                            ? role?.name
                                                ? role.name
                                                : "Aucun"
                                            : "Chargement..."
                                        : roleError}
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
                                    {new Date(
                                        profile.created_at
                                    ).toLocaleDateString()}
                                </span>
                            </div>
                        </div>{" "}
                    </>
                ) : (
                    <p>Chargement...</p>
                )
            ) : (
                <p>{factionError}</p>
            )}
        </div>
    );
}

export default Profile;
