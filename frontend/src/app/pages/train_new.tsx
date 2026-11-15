import axios from "axios";
import { useMemo, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";

import { useLines, useTrains } from "../components/hooks/trains";
import { useTrainRights } from "../components/hooks/trainrights";
import TrainBoard from "../components/snippets/train_board";
import { getErrorMessage } from "../utils/apierror";
import {
    COMMON_NAME_MAX,
    MAINTENANCE_LINE,
    SERVICES,
    firstFreeNumber,
    previewTrainName,
} from "../utils/trains";
import type { TrainService, TrainType } from "../types/trains";

/** Register a train: the name is built live, the number is given by the server. */
export default function TrainNewPage() {
    const navigate = useNavigate();
    const { lines } = useLines();
    const { user, factionId } = useTrainRights();

    const [line, setLine] = useState("");
    const [service, setService] = useState<TrainService | "">("");
    const [commonName, setCommonName] = useState("");
    const [legacyId, setLegacyId] = useState("");
    const [forFaction, setForFaction] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    const isMaintenance = line === MAINTENANCE_LINE;

    // The numbers already used on the line give the one the server will pick.
    const { trains: onLine } = useTrains({ line }, line !== "");
    const expected = useMemo(
        () =>
            line
                ? firstFreeNumber(onLine.map((t: TrainType) => t.number))
                : null,
        [line, onLine],
    );

    const ready = line !== "" && (isMaintenance || service !== "");

    const submit = async (event: FormEvent) => {
        event.preventDefault();
        if (!ready) {
            setError("Choisissez une ligne et un service.");
            return;
        }
        setSaving(true);
        setError("");
        try {
            const res = await axios.post<TrainType>("/trains", {
                line,
                service: isMaintenance ? null : service,
                common_name: commonName.trim() || null,
                legacy_id: legacyId.trim() || null,
                owner_faction_id: forFaction ? factionId : null,
            });
            await navigate(`/train/${res.data.train_id}`);
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="information-container">
            <div className="snippet-container">
                <h2>Enregistrer un train</h2>
                <p>
                    Le nom affiché en gare se construit en direct. Le numéro est
                    attribué automatiquement à l&apos;enregistrement.
                </p>

                <TrainBoard
                    name={previewTrainName(
                        line,
                        service,
                        ready ? expected : null,
                        commonName,
                    )}
                    line={line}
                    service={isMaintenance ? null : service}
                    number={ready ? expected : null}
                    numberNote={
                        ready && expected === null
                            ? "(ligne complète)"
                            : ready
                              ? "(attribué à l'enregistrement)"
                              : undefined
                    }
                />

                <form onSubmit={submit}>
                    <div className="modal-field">
                        <label htmlFor="train-line">Ligne</label>
                        <select
                            id="train-line"
                            value={line}
                            onChange={(e) => {
                                setLine(e.target.value);
                                if (e.target.value === MAINTENANCE_LINE) {
                                    setService("");
                                }
                            }}
                        >
                            <option value="">Choisir une ligne</option>
                            {lines
                                .filter((l) => l.code !== MAINTENANCE_LINE)
                                .map((l) => (
                                    <option key={l.code} value={l.code}>
                                        {l.code}
                                        {l.name ? ` - ${l.name}` : ""}
                                    </option>
                                ))}
                            <option value={MAINTENANCE_LINE}>
                                Z - Entretien
                            </option>
                        </select>
                        {lines.length === 0 && (
                            <small>
                                Aucune ligne n&apos;existe encore : un admin
                                trains ou une faction autorisée doit la créer (
                                <Link to="/lines">Lignes</Link>).
                            </small>
                        )}
                    </div>
                    <div className="modal-field">
                        <label htmlFor="train-service">Service</label>
                        <select
                            id="train-service"
                            value={service}
                            disabled={isMaintenance}
                            onChange={(e) =>
                                setService(e.target.value as TrainService | "")
                            }
                        >
                            <option value="">Choisir un service</option>
                            {(Object.keys(SERVICES) as TrainService[]).map(
                                (s) => (
                                    <option key={s} value={s}>
                                        {s} - {SERVICES[s]}
                                    </option>
                                ),
                            )}
                        </select>
                    </div>
                    <div className="modal-field">
                        <label htmlFor="train-common">
                            Nom commun (facultatif, {COMMON_NAME_MAX} caractères
                            max)
                        </label>
                        <input
                            id="train-common"
                            type="text"
                            maxLength={COMMON_NAME_MAX}
                            autoComplete="off"
                            placeholder="Aurore"
                            value={commonName}
                            onChange={(e) => setCommonName(e.target.value)}
                        />
                    </div>
                    <div className="modal-field">
                        <label htmlFor="train-legacy">
                            Ancien nom (facultatif)
                        </label>
                        <input
                            id="train-legacy"
                            type="text"
                            maxLength={50}
                            autoComplete="off"
                            placeholder="MMP1-1"
                            value={legacyId}
                            onChange={(e) => setLegacyId(e.target.value)}
                        />
                        <small>
                            Seulement pour un train déjà en circulation. Laissez
                            vide pour un train neuf.
                        </small>
                    </div>
                    <div className="modal-field">
                        <span>Propriétaire</span>
                        <label>
                            <input
                                type="radio"
                                name="owner"
                                checked={!forFaction}
                                onChange={() => setForFaction(false)}
                            />{" "}
                            Moi ({user?.username ?? "..."})
                        </label>
                        {factionId !== null && (
                            <label>
                                <input
                                    type="radio"
                                    name="owner"
                                    checked={forFaction}
                                    onChange={() => setForFaction(true)}
                                />{" "}
                                Ma faction
                            </label>
                        )}
                    </div>
                    {error && (
                        <p role="alert" className="train-form-error">
                            {error}
                        </p>
                    )}
                    <button
                        type="submit"
                        className="button"
                        disabled={saving || !ready}
                    >
                        {saving ? "Enregistrement..." : "Enregistrer le train"}
                    </button>{" "}
                    <Link className="button" to="/trains">
                        Annuler
                    </Link>
                </form>
            </div>
        </div>
    );
}
