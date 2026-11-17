import axios from "axios";
import { useState, type FormEvent } from "react";

import { getErrorMessage } from "../../utils/apierror";
import type { PlatformType } from "../../types/trains";

/** The platforms of a station; those who may change the station edit them. */
export default function PlatformsPanel({
    stationId,
    platforms,
    canManage,
    onChanged,
}: {
    stationId: number;
    platforms: PlatformType[];
    canManage: boolean;
    onChanged: () => void;
}) {
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");
    const [editing, setEditing] = useState<number | null>(null);
    const [editDescription, setEditDescription] = useState("");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");

    const run = async (action: () => Promise<unknown>): Promise<boolean> => {
        setBusy(true);
        setError("");
        try {
            await action();
            onChanged();
            return true;
        } catch (err) {
            setError(getErrorMessage(err));
            return false;
        } finally {
            setBusy(false);
        }
    };

    const add = async (event: FormEvent) => {
        event.preventDefault();
        const ok = await run(() =>
            axios.post(`/stations/${stationId}/platforms`, {
                name,
                description: description.trim() || null,
            }),
        );
        if (ok) {
            setName("");
            setDescription("");
        }
    };

    const saveDescription = async (platformId: number) => {
        const ok = await run(() =>
            axios.put(`/stations/${stationId}/platforms/${platformId}`, {
                description: editDescription.trim() || null,
            }),
        );
        if (ok) setEditing(null);
    };

    return (
        <div className="snippet-container">
            <h2>Quais</h2>
            {platforms.length === 0 ? (
                <p className="empty-state">Aucun quai renseigné.</p>
            ) : (
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Quai</th>
                                <th>Description</th>
                                {canManage && <th>Action</th>}
                            </tr>
                        </thead>
                        <tbody>
                            {platforms.map((p) => (
                                <tr key={p.platform_id}>
                                    <td>{p.name}</td>
                                    <td>
                                        {editing === p.platform_id ? (
                                            <input
                                                type="text"
                                                aria-label={`Description du quai ${p.name}`}
                                                maxLength={300}
                                                value={editDescription}
                                                onChange={(e) =>
                                                    setEditDescription(
                                                        e.target.value,
                                                    )
                                                }
                                            />
                                        ) : (
                                            (p.description ?? "-")
                                        )}
                                    </td>
                                    {canManage && (
                                        <td>
                                            {editing === p.platform_id ? (
                                                <>
                                                    <button
                                                        type="button"
                                                        className="button"
                                                        disabled={busy}
                                                        onClick={() =>
                                                            saveDescription(
                                                                p.platform_id,
                                                            )
                                                        }
                                                    >
                                                        Enregistrer
                                                    </button>{" "}
                                                    <button
                                                        type="button"
                                                        className="button"
                                                        onClick={() =>
                                                            setEditing(null)
                                                        }
                                                    >
                                                        Annuler
                                                    </button>
                                                </>
                                            ) : (
                                                <>
                                                    <button
                                                        type="button"
                                                        className="button"
                                                        onClick={() => {
                                                            setEditing(
                                                                p.platform_id,
                                                            );
                                                            setEditDescription(
                                                                p.description ??
                                                                    "",
                                                            );
                                                        }}
                                                    >
                                                        Modifier
                                                    </button>{" "}
                                                    <button
                                                        type="button"
                                                        className="button"
                                                        disabled={busy}
                                                        onClick={() =>
                                                            run(() =>
                                                                axios.delete(
                                                                    `/stations/${stationId}/platforms/${p.platform_id}`,
                                                                ),
                                                            )
                                                        }
                                                    >
                                                        Supprimer
                                                    </button>
                                                </>
                                            )}
                                        </td>
                                    )}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
            {canManage && (
                <form onSubmit={add} className="toolbar">
                    <input
                        type="text"
                        aria-label="Nom du quai"
                        placeholder="Nom (1, A...)"
                        maxLength={20}
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                    />
                    <input
                        type="text"
                        aria-label="Description du nouveau quai"
                        placeholder="Description (direction, accès...)"
                        maxLength={300}
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                    />
                    <button type="submit" className="button" disabled={busy}>
                        Ajouter un quai
                    </button>
                </form>
            )}
            {error && (
                <p role="alert" className="train-form-error">
                    {error}
                </p>
            )}
        </div>
    );
}
