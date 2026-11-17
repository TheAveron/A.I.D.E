import axios from "axios";
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";

import { getErrorMessage } from "../../utils/apierror";
import { parseCoordinate } from "../../utils/trains";
import { DIMENSIONS, type StationType } from "../../types/trains";

/** Change a station's name, place or description, or delete it. */
export default function StationEditor({
    station,
    onChanged,
}: {
    station: StationType;
    onChanged: () => void;
}) {
    const navigate = useNavigate();
    const [name, setName] = useState(station.name);
    const [x, setX] = useState(String(station.x));
    const [y, setY] = useState(station.y === null ? "" : String(station.y));
    const [z, setZ] = useState(String(station.z));
    const [dimension, setDimension] = useState<string>(station.dimension);
    const [description, setDescription] = useState(station.description ?? "");
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState("");

    const submit = async (event: FormEvent) => {
        event.preventDefault();
        const px = parseCoordinate(x);
        const pz = parseCoordinate(z);
        const py = y.trim() === "" ? null : parseCoordinate(y);
        if (px === null || pz === null || (y.trim() !== "" && py === null)) {
            setMessage("❌ Les coordonnées doivent être des nombres entiers.");
            return;
        }
        setBusy(true);
        setMessage("");
        try {
            await axios.put(`/stations/${station.station_id}`, {
                name,
                x: px,
                y: py,
                z: pz,
                dimension,
                description: description.trim() || null,
            });
            setMessage("✅ Gare modifiée");
            onChanged();
        } catch (err) {
            setMessage(`❌ ${getErrorMessage(err)}`);
        } finally {
            setBusy(false);
        }
    };

    const remove = async () => {
        if (!window.confirm(`Supprimer la gare ${station.name} ?`)) return;
        setBusy(true);
        setMessage("");
        try {
            await axios.delete(`/stations/${station.station_id}`);
            await navigate("/stations");
        } catch (err) {
            setMessage(`❌ ${getErrorMessage(err)}`);
            setBusy(false);
        }
    };

    return (
        <div className="snippet-container">
            <h2>Modifier la gare</h2>
            <form onSubmit={submit}>
                <div className="modal-field">
                    <label htmlFor="edit-station-name">Nom</label>
                    <input
                        id="edit-station-name"
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
                            value={x}
                            onChange={(e) => setX(e.target.value)}
                            required
                        />
                    </label>
                    <label>
                        Y{" "}
                        <input
                            type="text"
                            inputMode="numeric"
                            value={y}
                            onChange={(e) => setY(e.target.value)}
                        />
                    </label>
                    <label>
                        Z{" "}
                        <input
                            type="text"
                            inputMode="numeric"
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
                    <label htmlFor="edit-station-description">
                        Description
                    </label>
                    <textarea
                        id="edit-station-description"
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
                    Supprimer la gare
                </button>
            </form>
            {message && <p role="status">{message}</p>}
        </div>
    );
}
