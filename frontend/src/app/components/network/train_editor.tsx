import axios from "axios";
import { useState, type FormEvent } from "react";

import { useLines } from "../../hooks/network/trains";
import { getErrorMessage } from "../../utils/apierror";
import {
    COMMON_NAME_MAX,
    MAINTENANCE_LINE,
    SERVICES,
} from "../../utils/trains";
import type { TrainService, TrainType } from "../../types/trains";

/**
 * Change a train's line, service, names or owner, or retire it. The number
 * is never edited: the server keeps it on a service change and gives a new
 * one on a line change.
 */
export default function TrainEditor({
    train,
    userId,
    factionId,
    isTrainAdmin,
    onChanged,
}: {
    train: TrainType;
    userId: number;
    // The faction the user can register trains for (manage_trains), if any
    factionId: number | null;
    isTrainAdmin: boolean;
    onChanged: () => void;
}) {
    const { lines } = useLines();

    const [line, setLine] = useState(train.line);
    const [service, setService] = useState<TrainService | "">(
        train.service ?? "",
    );
    const [commonName, setCommonName] = useState(train.common_name ?? "");
    const [legacyId, setLegacyId] = useState(train.legacy_id ?? "");
    // "keep", "me" or "faction"
    const [owner, setOwner] = useState("keep");
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState("");

    const isMaintenance = line === MAINTENANCE_LINE;

    const submit = async (event: FormEvent) => {
        event.preventDefault();
        if (!isMaintenance && service === "") {
            setMessage("❌ Choisissez un service.");
            return;
        }

        const changes: Record<string, unknown> = {};
        if (line !== train.line) changes.line = line;
        const newService = isMaintenance ? null : service;
        if (newService !== train.service) changes.service = newService;
        if (commonName.trim() !== (train.common_name ?? "")) {
            changes.common_name = commonName.trim() || null;
        }
        if (legacyId.trim() !== (train.legacy_id ?? "")) {
            changes.legacy_id = legacyId.trim() || null;
        }
        if (owner === "me" && train.owner_user_id !== userId) {
            changes.owner_user_id = userId;
        }
        if (
            owner === "faction" &&
            factionId !== null &&
            train.owner_faction_id !== factionId
        ) {
            changes.owner_faction_id = factionId;
        }
        if (Object.keys(changes).length === 0) {
            setMessage("Rien à modifier.");
            return;
        }

        setSaving(true);
        setMessage("");
        try {
            await axios.put(`/trains/${train.train_id}`, changes);
            setOwner("keep");
            setMessage("✅ Train modifié");
            onChanged();
        } catch (err) {
            setMessage(`❌ ${getErrorMessage(err)}`);
        } finally {
            setSaving(false);
        }
    };

    const retire = async () => {
        if (
            !window.confirm(
                `Retirer le train ${train.display_name} ? Son numéro sera libéré.`,
            )
        ) {
            return;
        }
        setSaving(true);
        setMessage("");
        try {
            await axios.delete(`/trains/${train.train_id}`);
            onChanged();
        } catch (err) {
            setMessage(`❌ ${getErrorMessage(err)}`);
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="snippet-container">
            <h2>Modifier le train</h2>
            <form onSubmit={submit}>
                <div className="modal-field">
                    <label htmlFor="edit-line">Ligne</label>
                    <select
                        id="edit-line"
                        value={line}
                        onChange={(e) => setLine(e.target.value)}
                    >
                        {lines
                            .filter((l) => l.code !== MAINTENANCE_LINE)
                            .map((l) => (
                                <option key={l.code} value={l.code}>
                                    {l.code}
                                    {l.name ? ` - ${l.name}` : ""}
                                </option>
                            ))}
                        <option value={MAINTENANCE_LINE}>Z - Entretien</option>
                    </select>
                    {line !== train.line && (
                        <small>
                            Le train recevra le premier numéro libre de la ligne{" "}
                            {line} ; l&apos;historique garde l&apos;ancien nom.
                        </small>
                    )}
                </div>
                <div className="modal-field">
                    <label htmlFor="edit-service">Service</label>
                    <select
                        id="edit-service"
                        value={isMaintenance ? "" : service}
                        disabled={isMaintenance}
                        onChange={(e) =>
                            setService(e.target.value as TrainService | "")
                        }
                    >
                        <option value="">Choisir un service</option>
                        {(Object.keys(SERVICES) as TrainService[]).map((s) => (
                            <option key={s} value={s}>
                                {s} - {SERVICES[s]}
                            </option>
                        ))}
                    </select>
                </div>
                <div className="modal-field">
                    <label htmlFor="edit-common">Nom commun</label>
                    <input
                        id="edit-common"
                        type="text"
                        maxLength={COMMON_NAME_MAX}
                        value={commonName}
                        onChange={(e) => setCommonName(e.target.value)}
                    />
                </div>
                <div className="modal-field">
                    <label htmlFor="edit-legacy">Ancien nom</label>
                    <input
                        id="edit-legacy"
                        type="text"
                        maxLength={50}
                        value={legacyId}
                        onChange={(e) => setLegacyId(e.target.value)}
                    />
                </div>
                <div className="modal-field">
                    <label htmlFor="edit-owner">Propriétaire</label>
                    <select
                        id="edit-owner"
                        value={owner}
                        onChange={(e) => setOwner(e.target.value)}
                    >
                        <option value="keep">Inchangé</option>
                        <option value="me">Moi</option>
                        {factionId !== null && (
                            <option value="faction">Ma faction</option>
                        )}
                    </select>
                    {isTrainAdmin && (
                        <small>
                            Pour confier le train à un autre joueur ou à une
                            autre faction, passez par un admin trains via
                            l&apos;API.
                        </small>
                    )}
                </div>
                <button type="submit" className="button" disabled={saving}>
                    {saving ? "Enregistrement..." : "Enregistrer"}
                </button>{" "}
                <button
                    type="button"
                    className="button"
                    disabled={saving}
                    onClick={retire}
                >
                    Retirer le train
                </button>
            </form>
            {message && <p role="status">{message}</p>}
        </div>
    );
}
