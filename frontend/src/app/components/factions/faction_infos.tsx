import { useFaction } from "../../hooks/factions/faction";
import { useMe } from "../../hooks/users/me";
import { useRole } from "../../hooks/factions/role";
import { ApprovalToggle } from "./approvaltoggle";
import { DeleteFactionButton } from "./deletefaction";

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
    const { faction, loading, error, refresh } = useFaction(factionId ?? null);
    const { role } = useRole(user?.role_id ?? null);
    // Same rule as the API: managing roles of one's own faction
    const archived = !!faction?.deleted_at;
    const isLeader =
        role?.name === "Chef" &&
        role.faction_id === user?.faction_id &&
        user?.faction_id === faction?.faction_id;
    const canToggle =
        !!faction &&
        !archived &&
        user?.faction_id === faction.faction_id &&
        (role?.manage_roles ?? false);

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

                            {archived && (
                                <p role="status">
                                    Cette faction a été supprimée : seul son
                                    historique reste consultable.
                                </p>
                            )}

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
                                {isLeader && !archived && (
                                    <DeleteFactionButton
                                        factionId={faction.faction_id}
                                        factionName={faction.name}
                                    />
                                )}
                                {canToggle ? (
                                    <ApprovalToggle
                                        factionId={faction.faction_id}
                                        requiresApproval={
                                            faction.requires_approval
                                        }
                                        onChanged={refresh}
                                    />
                                ) : (
                                    <div className="info-row">
                                        <span className="info-label">
                                            Adhésion:
                                        </span>
                                        <span className="info-value-field">
                                            {faction.requires_approval
                                                ? "Sur demande"
                                                : "Libre"}
                                        </span>
                                    </div>
                                )}
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
