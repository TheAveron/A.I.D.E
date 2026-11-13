import { useFaction } from "../hooks/faction";
import { useMe } from "../hooks/me";
import { useRole } from "../hooks/role";

function FactionHead({
    faction_name,
    faction_id,
    user_faction_id,
    role_id,
}: {
    faction_name: string;
    faction_id: number;
    user_faction_id: number | null;
    role_id: number | null;
}) {
    const { role } = useRole(role_id ?? null);
    // Being "Chef" of another faction gives no right on this one.
    const canEdit = role?.name === "Chef" && user_faction_id === faction_id;

    return (
        <div className={"info-header" + (canEdit ? " editable" : "")}>
            <div className="info-title">{faction_name}</div>
            {canEdit && <div className="button">Edit</div>}
        </div>
    );
}

export default function FactionInfo({
    factionId,
}: {
    factionId: string | null;
}) {
    const { user } = useMe();
    const { faction, loading, error } = useFaction(factionId ?? null);

    return (
        <div className="snippet-container faction-page faction-container">
            {!error ? (
                !loading ? (
                    faction ? (
                        <>
                            <FactionHead
                                faction_name={faction.name}
                                faction_id={faction.faction_id}
                                user_faction_id={user?.faction_id ?? null}
                                role_id={user?.role_id ?? null}
                            />

                            <div className="info-values">
                                <div className="info-row">
                                    <span className="info-label">
                                        Description:
                                    </span>
                                    <span className="info-value-field">
                                        {faction.description ?? "Aucun"}
                                    </span>
                                </div>
                                <div className="info-row">
                                    <span className="info-label">
                                        Approuvée:
                                    </span>
                                    <span className="info-value-field">
                                        {faction.is_approved ? "Oui" : "Non"}
                                    </span>
                                </div>
                                <div className="info-row">
                                    <span className="info-label">
                                        Inscription:
                                    </span>
                                    <span className="info-value-field">
                                        {new Date(
                                            faction.created_at,
                                        ).toLocaleDateString()}
                                    </span>
                                </div>
                            </div>
                        </>
                    ) : (
                        <p>No faction data</p>
                    )
                ) : (
                    <p>Chargement de la faction...</p>
                )
            ) : (
                <p>{error}</p>
            )}
        </div>
    );
}
