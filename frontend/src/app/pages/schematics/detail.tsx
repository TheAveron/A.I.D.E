import axios from "axios";
import { useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router";

import { useSchematic } from "../../hooks/schematics/schematics";
import ComplianceBadge from "../../components/schematics/compliance_badge";
import SchematicPreview from "../../components/schematics/schematic_preview";
import TagInput from "../../components/schematics/tag_input";
import { getErrorMessage } from "../../utils/apierror";
import {
    COMMENT_MAX,
    MAX_NBT_BYTES,
    TITLE_MAX,
    downloadVersion,
    formatBytes,
    formatSize,
    nbtProblem,
    previewProblem,
} from "../../utils/schematics";
import type { SchematicType } from "../../types/schematics";

export default function SchematicPage() {
    const { schematicid } = useParams();
    const { schematic, loading, error, refresh } = useSchematic(schematicid);
    const [actionError, setActionError] = useState("");

    if (error) {
        return (
            <div className="information-container">
                <div className="snippet-container">
                    <p role="alert">{error}</p>
                    <Link className="button" to="/schematiques">
                        Retour à la galerie
                    </Link>
                </div>
            </div>
        );
    }
    if (loading && !schematic) return <p className="empty-state">Chargement…</p>;
    if (!schematic) return null;

    const current = schematic.current;

    const download = async (number: number) => {
        setActionError("");
        try {
            await downloadVersion(schematic.schematic_id, number);
        } catch (err) {
            setActionError(getErrorMessage(err));
        }
    };

    const setCompliance = async (number: number, compliant: boolean) => {
        setActionError("");
        try {
            await axios.put(
                `/schematics/${schematic.schematic_id}/versions/${number}/compliance`,
                { compliant },
            );
            refresh();
        } catch (err) {
            setActionError(getErrorMessage(err));
        }
    };

    return (
        <div className="information-container">
            <div className="snippet-container schematics-wide">
                <div className="offers-header">
                    <h2>{schematic.title}</h2>
                    <Link className="button" to="/schematiques">
                        Galerie
                    </Link>
                </div>

                <div className="schematic-detail">
                    <SchematicPreview
                        schematicId={schematic.schematic_id}
                        hasPreview={schematic.has_preview}
                        title={schematic.title}
                        version={schematic.updated_at}
                    />
                    <div className="schematic-detail-info">
                        {current?.compliant && <ComplianceBadge />}
                        <dl className="schematic-facts">
                            <dt>Auteur</dt>
                            <dd>
                                {schematic.author_user_id ? (
                                    <Link to={`/user/${schematic.author_user_id}`}>
                                        {schematic.author_name}
                                    </Link>
                                ) : (
                                    "un ancien joueur"
                                )}
                            </dd>
                            {current && (
                                <>
                                    <dt>Dimensions</dt>
                                    <dd>{formatSize(current)} blocs (x × y × z)</dd>
                                    <dt>Blocs</dt>
                                    <dd>{current.block_count.toLocaleString()}</dd>
                                    <dt>Version</dt>
                                    <dd>
                                        v{current.number} du{" "}
                                        {new Date(current.uploaded_at).toLocaleDateString()}
                                    </dd>
                                </>
                            )}
                        </dl>
                        {schematic.tags.length > 0 && (
                            <ul className="tag-list">
                                {schematic.tags.map((tag) => (
                                    <li key={tag}>
                                        <Link
                                            className="tag"
                                            to={`/schematiques?tag=${encodeURIComponent(tag)}`}
                                        >
                                            {tag}
                                        </Link>
                                    </li>
                                ))}
                            </ul>
                        )}
                        {current && (
                            <button
                                type="button"
                                className="button"
                                onClick={() => download(current.number)}
                            >
                                Télécharger ({formatBytes(current.size_bytes)})
                            </button>
                        )}
                    </div>
                </div>

                {schematic.description && (
                    <p className="schematic-description">{schematic.description}</p>
                )}
                {actionError && <p role="alert">{actionError}</p>}
            </div>

            <div className="snippet-container">
                <h2>Versions</h2>
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Version</th>
                                <th>Date</th>
                                <th>Par</th>
                                <th>Taille</th>
                                <th>Note</th>
                                <th>Normes</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {schematic.versions.map((v) => (
                                <tr key={v.number}>
                                    <td>v{v.number}</td>
                                    <td>{new Date(v.uploaded_at).toLocaleString()}</td>
                                    <td>{v.uploaded_by_name ?? "-"}</td>
                                    <td>
                                        {formatSize(v)}
                                        <br />
                                        <small>
                                            {v.block_count.toLocaleString()} blocs ·{" "}
                                            {formatBytes(v.size_bytes)}
                                        </small>
                                    </td>
                                    <td>{v.comment ?? ""}</td>
                                    <td>
                                        {schematic.can_review ? (
                                            <label>
                                                <input
                                                    type="checkbox"
                                                    checked={v.compliant}
                                                    onChange={(e) =>
                                                        setCompliance(
                                                            v.number,
                                                            e.target.checked,
                                                        )
                                                    }
                                                />{" "}
                                                Conforme
                                            </label>
                                        ) : v.compliant ? (
                                            "✓ Conforme"
                                        ) : (
                                            ""
                                        )}
                                    </td>
                                    <td>
                                        <button
                                            type="button"
                                            className="button"
                                            onClick={() => download(v.number)}
                                        >
                                            Télécharger
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                {schematic.can_review && (
                    <small>
                        Le badge « conforme aux normes » est propre à chaque version :
                        une nouvelle version doit être revérifiée.
                    </small>
                )}
            </div>

            {schematic.can_edit && (
                <ManagePanel schematic={schematic} onChange={refresh} />
            )}
        </div>
    );
}

/** What the author (or an admin) can do: edit, new version, preview, delete. */
function ManagePanel({
    schematic,
    onChange,
}: {
    schematic: SchematicType;
    onChange: () => void;
}) {
    const navigate = useNavigate();
    const id = schematic.schematic_id;

    const [title, setTitle] = useState(schematic.title);
    const [description, setDescription] = useState(schematic.description ?? "");
    const [tags, setTags] = useState(schematic.tags);
    const [file, setFile] = useState<File | null>(null);
    const [comment, setComment] = useState("");
    const [preview, setPreview] = useState<File | null>(null);
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");

    const run = async (action: () => Promise<unknown>, done: string) => {
        setBusy(true);
        setError("");
        setMessage("");
        try {
            await action();
            setMessage(done);
            onChange();
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setBusy(false);
        }
    };

    const saveInfo = (event: FormEvent) => {
        event.preventDefault();
        void run(
            () =>
                axios.put(`/schematics/${id}`, {
                    title: title.trim(),
                    description: description.trim() || null,
                    tags,
                }),
            "Informations enregistrées.",
        );
    };

    const uploadVersion = (event: FormEvent) => {
        event.preventDefault();
        const problem = nbtProblem(file);
        if (problem) {
            setError(problem);
            return;
        }
        const form = new FormData();
        form.append("file", file as File);
        if (comment.trim()) form.append("comment", comment.trim());
        void run(async () => {
            await axios.post(`/schematics/${id}/versions`, form);
            setFile(null);
            setComment("");
            (event.target as HTMLFormElement).reset();
        }, "Nouvelle version déposée.");
    };

    const replacePreview = (event: FormEvent) => {
        event.preventDefault();
        const problem = preview ? previewProblem(preview) : "Choisissez une image.";
        if (problem) {
            setError(problem);
            return;
        }
        const form = new FormData();
        form.append("preview", preview as File);
        void run(async () => {
            await axios.put(`/schematics/${id}/preview`, form);
            setPreview(null);
            (event.target as HTMLFormElement).reset();
        }, "Aperçu remplacé.");
    };

    const remove = async () => {
        if (
            !window.confirm(
                `Supprimer « ${schematic.title} » et ses ${schematic.version_count} version(s) ? C'est définitif.`,
            )
        ) {
            return;
        }
        setBusy(true);
        setError("");
        try {
            await axios.delete(`/schematics/${id}`);
            await navigate("/schematiques");
        } catch (err) {
            setError(getErrorMessage(err));
            setBusy(false);
        }
    };

    return (
        <div className="snippet-container schematics-wide">
            <h2>Gérer</h2>
            {message && <p className="schematic-success">{message}</p>}
            {error && <p role="alert">{error}</p>}

            <form onSubmit={saveInfo}>
                <h3>Informations</h3>
                <div className="modal-field">
                    <label htmlFor="edit-title">Titre</label>
                    <input
                        id="edit-title"
                        type="text"
                        required
                        maxLength={TITLE_MAX}
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                    />
                </div>
                <div className="modal-field">
                    <label htmlFor="edit-description">Description</label>
                    <textarea
                        id="edit-description"
                        rows={4}
                        maxLength={5000}
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                    />
                </div>
                <div className="modal-field">
                    <label htmlFor="edit-tags">Tags</label>
                    <TagInput id="edit-tags" value={tags} onChange={setTags} />
                </div>
                <button type="submit" className="button" disabled={busy}>
                    Enregistrer
                </button>
            </form>

            <form onSubmit={uploadVersion}>
                <h3>Nouvelle version</h3>
                <p>
                    Les versions précédentes restent téléchargeables. Le badge
                    « conforme aux normes » ne passe pas à la nouvelle version.
                </p>
                <div className="modal-field">
                    <label htmlFor="version-file">
                        Fichier .nbt ({formatBytes(MAX_NBT_BYTES)} max)
                    </label>
                    <input
                        id="version-file"
                        type="file"
                        accept=".nbt"
                        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                    />
                </div>
                <div className="modal-field">
                    <label htmlFor="version-comment">
                        Ce qui change (facultatif)
                    </label>
                    <input
                        id="version-comment"
                        type="text"
                        maxLength={COMMENT_MAX}
                        placeholder="Quai allongé à 24 blocs"
                        value={comment}
                        onChange={(e) => setComment(e.target.value)}
                    />
                </div>
                <button type="submit" className="button" disabled={busy}>
                    Déposer la version
                </button>
            </form>

            <form onSubmit={replacePreview}>
                <h3>Aperçu</h3>
                <div className="modal-field">
                    <label htmlFor="preview-file">
                        Nouvelle image (PNG, JPEG ou WebP)
                    </label>
                    <input
                        id="preview-file"
                        type="file"
                        accept="image/png,image/jpeg,image/webp"
                        onChange={(e) => setPreview(e.target.files?.[0] ?? null)}
                    />
                </div>
                <div className="offers-header">
                    <button type="submit" className="button" disabled={busy}>
                        {schematic.has_preview ? "Remplacer l'aperçu" : "Ajouter l'aperçu"}
                    </button>
                    {schematic.has_preview && (
                        <button
                            type="button"
                            className="button"
                            disabled={busy}
                            onClick={() =>
                                void run(
                                    () => axios.delete(`/schematics/${id}/preview`),
                                    "Aperçu retiré.",
                                )
                            }
                        >
                            Retirer l&apos;aperçu
                        </button>
                    )}
                </div>
            </form>

            <div>
                <h3>Supprimer</h3>
                <button
                    type="button"
                    className="button button-danger"
                    disabled={busy}
                    onClick={() => void remove()}
                >
                    Supprimer le schematic
                </button>
            </div>
        </div>
    );
}
