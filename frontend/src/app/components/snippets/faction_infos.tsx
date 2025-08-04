import { useParams } from "react-router-dom";
import { useFaction } from "../hooks/faction";
import { useMe } from "../hooks/me";
import { useRole } from "../hooks/role";

import "../../../assets/css/components/info.css";
import "../../../assets/css/components/buttons.css";

function FactionHead({
    faction_name,
    role_id,
}: {
    faction_name: string;
    role_id: string | undefined;
}) {
    const { role } = useRole(role_id ?? null);

    if (role?.name === "Chief") {
        return (
            <div className="info-header editable">
                <div className="info-title">{faction_name}</div>
                <div className="button">Edit</div>
            </div>
        );
    }
    return <></>;
}

export default function FactionInfo() {
    const { user } = useMe();
    const { factionid } = useParams();
    const { faction, loading: FactionLoading } = useFaction(factionid ?? null);

    if (!factionid) {
        return <p>No faction id provided</p>;
    }

    if (!faction?.name) {
        return <p>No faction id provided</p>;
    }

    return (
        <div className="snippet-container faction-page faction-container">
            {FactionLoading ? (
                <p>Chargement de la faction...</p>
            ) : (
                <>
                    <FactionHead
                        faction_name={faction?.name}
                        role_id={user?.role_id?.toString()}
                    />

                    {faction ? (
                        <div className="info-values">
                            <div className="info-row">
                                <span className="info-label">Description:</span>
                                <span className="info-value-field">
                                    {faction.description ?? "Aucun"}
                                </span>
                            </div>
                            <div className="info-row">
                                <span className="info-label">Approuvée:</span>
                                <span className="info-value-field">
                                    {faction.is_approved ? "Oui" : "Non"}
                                </span>
                            </div>
                            <div className="info-row">
                                <span className="info-label">Inscription:</span>
                                <span className="info-value-field">
                                    {new Date(
                                        faction.created_at
                                    ).toLocaleDateString()}
                                </span>
                            </div>
                        </div>
                    ) : (
                        <p>No faction data</p>
                    )}
                </>
            )}
        </div>
    );
}
