import axios from "axios";
import { useState, type FormEvent } from "react";

import { getErrorMessage } from "../../utils/apierror";

// The server's limits (schemas/factions.py, schemas/base.py)
const NAME_MAX = 100;
const DESCRIPTION_MAX = 5000;

/**
 * Why the draft can't be sent, or "" when it can. The server checks it again
 * (and alone knows whether a similar name is taken: 409).
 */
function validateFactionDraft(name: string, description: string): string {
    const trimmed = name.trim();
    if (!trimmed) return "Le nom est obligatoire.";
    if (trimmed.length > NAME_MAX) {
        return `Le nom ne peut pas dépasser ${NAME_MAX} caractères.`;
    }
    // The server names the documents folder after normalize(name), which
    // drops digits and punctuation: a name needs at least one letter.
    if (!/\p{L}/u.test(trimmed)) {
        return "Le nom doit contenir au moins une lettre.";
    }
    if (description.trim().length > DESCRIPTION_MAX) {
        return `La description ne peut pas dépasser ${DESCRIPTION_MAX} caractères.`;
    }
    return "";
}

/**
 * Change a faction's name and description (needs manage_roles in it, like
 * the API). Only the fields that changed are sent: renaming moves the
 * faction's documents folder on the server, so a name left as it is must not
 * be sent.
 */
export function FactionEditor({
    factionId,
    name,
    description,
    onDone,
}: {
    factionId: number;
    name: string;
    description: string | null;
    onDone: (changed: boolean) => void;
}) {
    const [draftName, setDraftName] = useState(name);
    const [draftDescription, setDraftDescription] = useState(description ?? "");
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    const submit = async (event: FormEvent) => {
        event.preventDefault();
        const problem = validateFactionDraft(draftName, draftDescription);
        if (problem) {
            setError(problem);
            return;
        }

        const body: { name?: string; description?: string | null } = {};
        const newName = draftName.trim();
        const newDescription = draftDescription.trim() || null;
        if (newName !== name) body.name = newName;
        if (newDescription !== (description ?? null)) {
            body.description = newDescription;
        }
        if (Object.keys(body).length === 0) {
            onDone(false);
            return;
        }

        setSaving(true);
        setError("");
        try {
            await axios.put(`/factions/update/${factionId}`, body);
            onDone(true);
        } catch (err) {
            setError(
                axios.isAxiosError(err) && err.response?.status === 409
                    ? "Une faction porte déjà un nom trop proche."
                    : getErrorMessage(err),
            );
            setSaving(false);
        }
    };

    return (
        <form onSubmit={submit}>
            <div className="modal-field">
                <label htmlFor="faction-name">Nom</label>
                <input
                    id="faction-name"
                    type="text"
                    maxLength={NAME_MAX}
                    value={draftName}
                    onChange={(e) => setDraftName(e.target.value)}
                />
            </div>
            <div className="modal-field">
                <label htmlFor="faction-description">Description</label>
                <textarea
                    id="faction-description"
                    rows={4}
                    maxLength={DESCRIPTION_MAX}
                    value={draftDescription}
                    onChange={(e) => setDraftDescription(e.target.value)}
                />
            </div>
            <button type="submit" className="button" disabled={saving}>
                {saving ? "Enregistrement..." : "Enregistrer"}
            </button>{" "}
            <button
                type="button"
                className="button"
                disabled={saving}
                onClick={() => onDone(false)}
            >
                Annuler
            </button>
            {error && <p role="alert">{error}</p>}
        </form>
    );
}
