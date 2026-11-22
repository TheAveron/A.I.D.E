import { useState } from "react";
import { useRoles } from "../../hooks/factions/factionroles";
import { useUpdateUser } from "../../hooks/factions/role";

interface UpdateFactionButtonProps {
    userId: number;
    currentFactionId: number | null;
    currentRoleId: number | null;
    factionId: number;
    factionName: string;
    // The faction (and role) the user leaves by joining, if any
    currentFactionName: string | null;
    onUpdate?: () => void;
}

export function UpdateFactionButton({
    userId,
    currentFactionId,
    currentRoleId,
    factionId,
    factionName,
    currentFactionName,
    onUpdate,
}: UpdateFactionButtonProps) {
    const {
        roles: currentFactionRoles,
        loading: currentRolesLoading,
        error: currentRolesError,
    } = useRoles(currentFactionId?.toString() ?? null);

    const {
        roles: newFactionRoles,
        loading: newRolesLoading,
        error: newRolesError,
    } = useRoles(factionId.toString());

    const {
        updateUser,
        loading: updateLoading,
        error: updateError,
    } = useUpdateUser();

    const [message, setMessage] = useState<string | null>(null);

    const currentRole = currentFactionRoles?.find(
        (r) => r.role_id === currentRoleId,
    );

    const userHasChefRole = currentRole?.name === "Chef";

    const inviteRole = newFactionRoles?.find((r) => r.name === "Invité");

    const handleClick = async () => {
        setMessage(null);

        if (userHasChefRole) {
            setMessage("L'utilisateur est Chef dans sa faction actuelle.");
            return;
        }

        if (!inviteRole) {
            setMessage("Le rôle 'Invité' est introuvable dans cette faction.");
            return;
        }

        const question = currentFactionName
            ? `Rejoindre « ${factionName} » ? Vous quitterez « ${currentFactionName} » et votre rôle actuel.`
            : `Rejoindre « ${factionName} » ?`;
        if (!window.confirm(question)) return;

        try {
            const updatedUser = await updateUser(userId, {
                faction_id: factionId,
                role_id: inviteRole.role_id,
            });

            if (updatedUser) {
                // The row loses its button once the user is in the faction
                onUpdate?.();
            } else {
                setMessage("Erreur lors de la mise à jour de l'utilisateur.");
            }
        } catch {
            setMessage("Erreur lors de la mise à jour.");
        }
    };

    const isLoading = currentRolesLoading || newRolesLoading || updateLoading;

    return (
        <div>
            <button onClick={handleClick} disabled={isLoading}>
                {isLoading ? "Mise à jour..." : "Rejoindre"}
            </button>

            {message && <p>{message}</p>}

            {(currentRolesError || newRolesError || updateError) && (
                <p style={{ color: "red" }}>
                    {currentRolesError || newRolesError || updateError}
                </p>
            )}
        </div>
    );
}
