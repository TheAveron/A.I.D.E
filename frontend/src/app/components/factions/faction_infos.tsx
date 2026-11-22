import { useFaction } from "../../hooks/factions/faction";
import { useMe } from "../../hooks/users/me";
import { useRole } from "../../hooks/factions/role";
import { ApprovalToggle } from "./approvaltoggle";
import { DeleteFactionButton } from "./deletefaction";
import { FactionEditor } from "./faction_editor";
import { useState } from "react";
import { isLeaderRole } from "../../utils/roles";

function FactionHead({
    faction_name,
    onEdit,
}: {
    faction_name: string;
    // Shown only to those who may change the faction (null: nobody here)
    onEdit: (() => void) | null;
}) {
    return (
        <div className={"info-header" + (onEdit ? " editable" : "")}>
            <div className="info-title">{faction_name}</div>
            {onEdit && (
                <button type="button" className="button" onClick={onEdit}>
                    Modifier
                </button>
            )}
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
    const archived = !!faction?.deleted_at;
    // The leader of this very faction (being "Chef" elsewhere gives nothing)
    const isLeader =
        isLeaderRole(role) &&
        role?.faction_id === user?.faction_id &&
        user?.faction_id === faction?.faction_id;
    const [editing, setEditing] = useState(false);
    // Same rule as the API (PUT /factions/update): manage_roles in this faction
    const canEdit =
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
                                onEdit={
                                    canEdit && !editing
                                        ? () => setEditing(true)
                                        : null
                                }
                            />

                            {editing && canEdit && (
                                <FactionEditor
                                    factionId={faction.faction_id}
                                    name={faction.name}
                                    description={faction.description}
                                    onDone={(changed) => {
                                        setEditing(false);
                                        if (changed) refresh();
                                    }}
                                />
                            )}

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
                                {canEdit ? (
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
                        <p>Faction introuvable.</p>
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
