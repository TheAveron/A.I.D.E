import axios from "axios";
import { useState } from "react";

import { getErrorMessage } from "../../utils/apierror";

/** Choose whether a faction takes members on request only (needs manage_roles). */
export function ApprovalToggle({
    factionId,
    requiresApproval,
    onChanged,
}: {
    factionId: number;
    requiresApproval: boolean;
    onChanged: () => void;
}) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const change = async (value: boolean) => {
        setLoading(true);
        setError(null);
        try {
            await axios.put(`/factions/update/${factionId}`, {
                requires_approval: value,
            });
            onChanged();
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="info-row">
            <label>
                <input
                    type="checkbox"
                    checked={requiresApproval}
                    disabled={loading}
                    onChange={(e) => change(e.target.checked)}
                />{" "}
                Adhésion sur demande uniquement
            </label>
            {error && <p role="alert">{error}</p>}
        </div>
    );
}
