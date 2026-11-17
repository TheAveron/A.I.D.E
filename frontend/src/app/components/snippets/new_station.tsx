import axios from "axios";
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";

import { getErrorMessage } from "../../utils/apierror";
import { parseCoordinate, parsePlatforms } from "../../utils/trains";
import { DIMENSIONS, type StationType } from "../../types/trains";

/** Register a station: anybody may, the coordinates are required. */
export default function NewStation() {
    const navigate = useNavigate();
    const [name, setName] = useState("");
    const [x, setX] = useState("");
    const [y, setY] = useState("");
    const [z, setZ] = useState("");
    const [dimension, setDimension] = useState("overworld");
    const [description, setDescription] = useState("");
    const [platforms, setPlatforms] = useState("");
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    const submit = async (event: FormEvent) => {
        event.preventDefault();
        const px = parseCoordinate(x);
        const pz = parseCoordinate(z);
        const py = y.trim() === "" ? null : parseCoordinate(y);
        if (px === null || pz === null || (y.trim() !== "" && py === null)) {
            setError("Les coordonnées doivent être des nombres entiers.");
            return;
        }
        setSaving(true);
        setError("");
        try {
            const res = await axios.post<StationType>("/stations", {
                name,
                x: px,
                y: py,
                z: pz,
                dimension,
                description: description.trim() || null,
                platforms: parsePlatforms(platforms),
            });
            await navigate(`/station/${res.data.station_id}`);
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="snippet-container">
            <h2>Enregistrer une gare</h2>
            <form onSubmit={submit}>
                <div className="modal-field">
                    <label htmlFor="station-name">Nom</label>
                    <input
                        id="station-name"
                        type="text"
                        maxLength={60}
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                    />
                </div>
                <div className="toolbar">
                    <label>
                        X{" "}
                        <input
                            type="text"
                            inputMode="numeric"
                            aria-label="Coordonnée X"
                            value={x}
                            onChange={(e) => setX(e.target.value)}
                            required
                        />
                    </label>
                    <label>
                        Y (hauteur, facultatif){" "}
                        <input
                            type="text"
                            inputMode="numeric"
                            aria-label="Coordonnée Y"
                            value={y}
                            onChange={(e) => setY(e.target.value)}
                        />
                    </label>
                    <label>
                        Z{" "}
                        <input
                            type="text"
                            inputMode="numeric"
                            aria-label="Coordonnée Z"
                            value={z}
                            onChange={(e) => setZ(e.target.value)}
                            required
                        />
                    </label>
                    <select
                        aria-label="Dimension"
                        value={dimension}
                        onChange={(e) => setDimension(e.target.value)}
                    >
                        {Object.entries(DIMENSIONS).map(([value, label]) => (
                            <option key={value} value={value}>
                                {label}
                            </option>
                        ))}
                    </select>
                </div>
                <div className="modal-field">
                    <label htmlFor="station-description">
                        Description (facultatif)
                    </label>
                    <textarea
                        id="station-description"
                        rows={2}
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                    />
                </div>
                <div className="modal-field">
                    <label htmlFor="station-platforms">
                        Quais (facultatif, un par ligne : « nom : description »)
                    </label>
                    <textarea
                        id="station-platforms"
                        rows={3}
                        placeholder={
                            "1 : vers le nord, de plain-pied\nA : escalier"
                        }
                        value={platforms}
                        onChange={(e) => setPlatforms(e.target.value)}
                    />
                </div>
                {error && (
                    <p role="alert" className="train-form-error">
                        {error}
                    </p>
                )}
                <button type="submit" className="button" disabled={saving}>
                    {saving ? "Enregistrement..." : "Enregistrer la gare"}
                </button>
            </form>
        </div>
    );
}
