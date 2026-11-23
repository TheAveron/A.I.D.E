import axios from "axios";
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";

import FormDialog from "../common/form_dialog";
import { getErrorMessage } from "../../utils/apierror";
import { isLineCode } from "../../utils/trains";

/** Create a line: train admins, and factions with manage_trains. */
export default function NewLine() {
    const navigate = useNavigate();
    const [code, setCode] = useState("");
    const [name, setName] = useState("");
    const [useColor, setUseColor] = useState(false);
    const [color, setColor] = useState("#1ea2a9");
    const [description, setDescription] = useState("");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");

    const submit = async (event: FormEvent) => {
        event.preventDefault();
        const line = code.trim().toUpperCase();
        if (!isLineCode(line) || line === "Z") {
            setError(
                "Une ligne est une lettre de A à Y, suivie d'un chiffre de 1 à 9 pour un embranchement (A, A2).",
            );
            return;
        }
        setBusy(true);
        setError("");
        try {
            await axios.post("/lines", {
                code: line,
                name: name.trim() || null,
                color: useColor ? color : null,
                description: description.trim() || null,
            });
            await navigate(`/line/${line}`);
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setBusy(false);
        }
    };

    return (
        <FormDialog label="Créer une ligne" title="Créer une ligne">
            <form onSubmit={submit}>
                <div className="toolbar">
                    <input
                        type="text"
                        aria-label="Code de la ligne"
                        placeholder="A ou A2"
                        maxLength={2}
                        autoFocus
                        value={code}
                        onChange={(e) => setCode(e.target.value.toUpperCase())}
                        required
                    />
                    <input
                        type="text"
                        aria-label="Nom de la ligne"
                        placeholder="Nom (facultatif)"
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
                    <label htmlFor="line-description">
                        Description (facultatif)
                    </label>
                    <textarea
                        id="line-description"
                        rows={2}
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                    />
                </div>
                {error && (
                    <p role="alert" className="train-form-error">
                        {error}
                    </p>
                )}
                <button type="submit" className="button" disabled={busy}>
                    Créer la ligne
                </button>
            </form>
        </FormDialog>
    );
}
