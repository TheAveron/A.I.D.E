import axios from "axios";
import { useState } from "react";
import { useNavigate } from "react-router";

import { getErrorMessage } from "../../utils/apierror";
import { useMe } from "../hooks/me";
import { useMemberCounts } from "../hooks/member_counts";

/**
 * The leader deletes their faction: it is archived, every member goes back to
 * "Sans Faction" and its open offers are cancelled. The name has to be typed
 * to confirm, as there is no way back.
 */
export function DeleteFactionButton({
    factionId,
    factionName,
}: {
    factionId: number;
    factionName: string;
}) {
    const navigate = useNavigate();
    const { refresh: refreshMe } = useMe();
    const { refresh: refreshCounts } = useMemberCounts();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const onClick = async () => {
        const typed = window.prompt(
            `Supprimer la faction « ${factionName} » ?\n` +
                "Tous les membres (vous compris) seront sans faction et ses " +
                "offres ouvertes annulées.\n\nTapez son nom pour confirmer :",
        );
        if (typed === null) return;
        if (typed.trim() !== factionName) {
            setError("Le nom saisi ne correspond pas : suppression annulée.");
            return;
        }

        setLoading(true);
        setError("");
        try {
            await axios.delete(`/factions/delete/${factionId}`);
            refreshMe();
            refreshCounts();
            navigate("/factions");
        } catch (err) {
            setError(getErrorMessage(err));
            setLoading(false);
        }
    };

    return (
        <div className="info-row">
            <button
                type="button"
                className="button"
                disabled={loading}
                onClick={onClick}
            >
                Supprimer la faction
            </button>
            {error && <p role="alert">{error}</p>}
        </div>
    );
}
