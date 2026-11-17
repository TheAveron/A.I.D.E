import axios from "axios";
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";

import { getErrorMessage } from "../../utils/apierror";
import type { LineType } from "../../types/trains";

/** Change a line's name, colour or description, or delete it. */
export default function LineEditor({
    line,
    onChanged,
}: {
    line: LineType;
    onChanged: () => void;
}) {
    const navigate = useNavigate();
    const [name, setName] = useState(line.name ?? "");
    const [useColor, setUseColor] = useState(line.color !== null);
    const [color, setColor] = useState(line.color ?? "#1ea2a9");
    const [description, setDescription] = useState(line.description ?? "");
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState("");

    const submit = async (event: FormEvent) => {
        event.preventDefault();
        setBusy(true);
        setMessage("");
        try {
            await axios.put(`/lines/${line.code}`, {
                name: name.trim() || null,
                color: useColor ? color : null,
                description: description.trim() || null,
            });
            setMessage("✅ Ligne modifiée");
            onChanged();
        } catch (err) {
            setMessage(`❌ ${getErrorMessage(err)}`);
        } finally {
            setBusy(false);
        }
    };

    const remove = async () => {
        if (!window.confirm(`Supprimer la ligne ${line.code} ?`)) return;
        setBusy(true);
        setMessage("");
        try {
            await axios.delete(`/lines/${line.code}`);
            await navigate("/lines");
        } catch (err) {
            setMessage(`❌ ${getErrorMessage(err)}`);
            setBusy(false);
        }
    };

    return (
        <div className="snippet-container">
            <h2>Modifier la ligne</h2>
            <form onSubmit={submit}>
                <div className="toolbar">
                    <input
                        type="text"
                        aria-label="Nom de la ligne"
                        placeholder="Nom"
                        maxLength={60}
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                    />
                    <label>
                        <input
                            type="checkbox"
                            checked={useColor}
                            onChange={(e) => setUseColor(e.target.checked)}
                        />{" "}
                        Couleur{" "}
                        <input
                            type="color"
                            aria-label="Couleur de la ligne"
                            value={color}
                            disabled={!useColor}
                            onChange={(e) => setColor(e.target.value)}
                        />
                    </label>
                </div>
                <div className="modal-field">
                    <label htmlFor="edit-line-description">Description</label>
                    <textarea
                        id="edit-line-description"
                        rows={2}
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                    />
                </div>
                <button type="submit" className="button" disabled={busy}>
                    Enregistrer
                </button>{" "}
                <button
                    type="button"
                    className="button"
                    disabled={busy}
                    onClick={remove}
                >
                    Supprimer la ligne
                </button>
            </form>
            {message && <p role="status">{message}</p>}
        </div>
    );
}
