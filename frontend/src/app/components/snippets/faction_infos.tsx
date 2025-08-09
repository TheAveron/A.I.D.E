import { useFaction } from "../hooks/faction";
import { useMe } from "../hooks/me";
import { useRole } from "../hooks/role";

function FactionHead({
    faction_name,
    role_id,
}: {
    faction_name: string;
    role_id: number | null;
}) {
    const { role } = useRole(role_id ?? null);
    let editableText = "";

    if (role?.name === "Chef") {
        editableText = " editable";
    }

    return (
        <div className={"info-header" + editableText}>
            <div className="info-title">{faction_name}</div>
            {role?.name === "Chef" ? <div className="button">Edit</div> : <></>}
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
                                faction_name={faction?.name}
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
                                            faction.created_at
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
