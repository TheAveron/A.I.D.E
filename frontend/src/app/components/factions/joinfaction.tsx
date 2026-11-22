import { useUpdateUser } from "../../hooks/factions/role";

interface UpdateFactionButtonProps {
    userId: number;
    factionId: number;
    factionName: string;
    // The faction (and role) the user leaves by joining, if any
    currentFactionName: string | null;
    onUpdate?: () => void;
}

/**
 * Join a faction that takes members freely. The server gives its "Membre"
 * role: only the faction is sent. (A leader never sees this button: the
 * factions table hides the column for them.)
 */
export function UpdateFactionButton({
    userId,
    factionId,
    factionName,
    currentFactionName,
    onUpdate,
}: UpdateFactionButtonProps) {
    const { updateUser, loading, error } = useUpdateUser();

    const handleClick = async () => {
        const question = currentFactionName
            ? `Rejoindre « ${factionName} » ? Vous quitterez « ${currentFactionName} » et votre rôle actuel.`
            : `Rejoindre « ${factionName} » ?`;
        if (!window.confirm(question)) return;

        // The row loses its button once the user is in the faction
        if (await updateUser(userId, { faction_id: factionId })) onUpdate?.();
    };

    return (
        <div>
            <button
                type="button"
                className="button"
                onClick={handleClick}
                disabled={loading}
            >
                {loading ? "Mise à jour..." : "Rejoindre"}
            </button>
            {error && <p role="alert">{error}</p>}
        </div>
    );
}
