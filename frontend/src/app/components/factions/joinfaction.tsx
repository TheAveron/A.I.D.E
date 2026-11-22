import axios from "axios";
import { useState } from "react";

import { useUpdateUser } from "../../hooks/factions/role";
import { getErrorMessage } from "../../utils/apierror";
import type { RoleType } from "../../types/roles";
import { isGuestRole } from "../../utils/roles";

interface UpdateFactionButtonProps {
    userId: number;
    factionId: number;
    factionName: string;
    // The faction (and role) the user leaves by joining, if any
    currentFactionName: string | null;
    onUpdate?: () => void;
}

/**
 * Join a faction that takes members freely, as its "Invité". Its roles are
 * only fetched on the click: the list has one such button per row. (A leader
 * never sees it: the factions table hides the column for them.)
 */
export function UpdateFactionButton({
    userId,
    factionId,
    factionName,
    currentFactionName,
    onUpdate,
}: UpdateFactionButtonProps) {
    const {
        updateUser,
        loading: updating,
        error: updateError,
    } = useUpdateUser();
    const [fetching, setFetching] = useState(false);
    const [message, setMessage] = useState<string | null>(null);

    const handleClick = async () => {
        setMessage(null);

        const question = currentFactionName
            ? `Rejoindre « ${factionName} » ? Vous quitterez « ${currentFactionName} » et votre rôle actuel.`
            : `Rejoindre « ${factionName} » ?`;
        if (!window.confirm(question)) return;

        let inviteRole: RoleType | undefined;
        setFetching(true);
        try {
            const { data } = await axios.get<RoleType[]>(
                `/roles/faction/${factionId}`,
            );
            inviteRole = data.find(isGuestRole);
        } catch (err) {
            setMessage(getErrorMessage(err));
            return;
        } finally {
            setFetching(false);
        }

        if (!inviteRole) {
            setMessage(
                "Le rôle « Invité » est introuvable dans cette faction.",
            );
            return;
        }

        const updatedUser = await updateUser(userId, {
            faction_id: factionId,
            role_id: inviteRole.role_id,
        });
        // The row loses its button once the user is in the faction
        if (updatedUser) onUpdate?.();
    };

    const busy = fetching || updating;

    return (
        <div>
            <button
                type="button"
                className="button"
                onClick={handleClick}
                disabled={busy}
            >
                {busy ? "Mise à jour..." : "Rejoindre"}
            </button>
            {(message || updateError) && (
                <p role="alert">{message || updateError}</p>
            )}
        </div>
    );
}
