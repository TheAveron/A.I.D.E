import axios from "axios";
import { useState } from "react";

import { getErrorMessage } from "../../utils/apierror";
import { useMe } from "../../hooks/users/me";

/**
 * The leader hands the faction over to a member; they become "Chef Adjoint"
 * themselves. Asked twice (a confirmation), as only the new leader can undo it.
 */
export function TransferLeadershipButton({
    factionId,
    userId,
    username,
    onDone,
}: {
    factionId: number;
    userId: number;
    username: string;
    onDone: () => void;
}) {
    const { refresh: refreshMe } = useMe();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const onClick = async () => {
        if (
            !window.confirm(
                `Nommer ${username} chef de la faction ? Vous deviendrez chef adjoint et seul ${username} pourra annuler.`,
            )
        )
            return;
        setLoading(true);
        setError("");
        try {
            await axios.post(`/factions/transfer/${factionId}`, {
                user_id: userId,
            });
            refreshMe();
            onDone();
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <button
                type="button"
                className="button"
                disabled={loading}
                onClick={onClick}
            >
                Nommer chef
            </button>
            {error && <p role="alert">{error}</p>}
        </>
    );
}
