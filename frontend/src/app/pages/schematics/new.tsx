import axios from "axios";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";

import TagInput from "../../components/schematics/tag_input";
import { getErrorMessage } from "../../utils/apierror";
import {
    MAX_NBT_BYTES,
    MAX_PREVIEW_BYTES,
    TITLE_MAX,
    formatBytes,
    nbtProblem,
    previewProblem,
} from "../../utils/schematics";
import type { SchematicType } from "../../types/schematics";

/** Upload a schematic: the file, a title, tags, and optionally a preview. */
export default function SchematicNewPage() {
    const navigate = useNavigate();
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [tags, setTags] = useState<string[]>([]);
    const [file, setFile] = useState<File | null>(null);
    const [preview, setPreview] = useState<File | null>(null);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    const submit = async (event: FormEvent) => {
        event.preventDefault();
        const problem =
            (title.trim() ? "" : "Donnez un titre.") ||
            nbtProblem(file) ||
            previewProblem(preview);
        if (problem) {
            setError(problem);
            return;
        }
        const form = new FormData();
        form.append("title", title.trim());
        if (description.trim()) form.append("description", description.trim());
        form.append("tags", tags.join(","));
        form.append("file", file as File);
        if (preview) form.append("preview", preview);

        setSaving(true);
        setError("");
        try {
            const res = await axios.post<SchematicType>("/schematics", form);
            await navigate(`/schematique/${res.data.schematic_id}`);
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="information-container">
            <div className="snippet-container">
                <h2>Déposer un schematic</h2>
                <p>
                    Un fichier <code>.nbt</code> enregistré avec la Schematic
                    and Quill de Create ou un bloc de structure. Ses dimensions
                    sont lues automatiquement.
                </p>

                <form onSubmit={submit}>
                    <div className="modal-field">
                        <label htmlFor="schematic-file">
                            Fichier .nbt ({formatBytes(MAX_NBT_BYTES)} max)
                        </label>
                        <input
                            id="schematic-file"
                            type="file"
                            accept=".nbt"
                            required
                            onChange={(e) => {
                                const chosen = e.target.files?.[0] ?? null;
                                setFile(chosen);
                                setError(chosen ? nbtProblem(chosen) : "");
                                if (chosen && !title) {
                                    setTitle(
                                        chosen.name
                                            .replace(/\.nbt$/i, "")
                                            .replace(/[_-]+/g, " ")
                                            .slice(0, TITLE_MAX),
                                    );
                                }
                            }}
                        />
                    </div>
                    <div className="modal-field">
                        <label htmlFor="schematic-title">Titre</label>
                        <input
                            id="schematic-title"
                            type="text"
                            required
                            maxLength={TITLE_MAX}
                            autoComplete="off"
                            placeholder="Gare de passage à quai latéral"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                        />
                    </div>
                    <div className="modal-field">
                        <label htmlFor="schematic-description">
                            Description (facultatif)
                        </label>
                        <textarea
                            id="schematic-description"
                            rows={4}
                            maxLength={5000}
                            placeholder="Ce qu'il faut savoir pour la poser : orientation, matériaux, réglages…"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                        />
                    </div>
                    <div className="modal-field">
                        <label htmlFor="schematic-tags">Tags</label>
                        <TagInput
                            id="schematic-tags"
                            value={tags}
                            onChange={setTags}
                        />
                    </div>
                    <div className="modal-field">
                        <label htmlFor="schematic-preview">
                            Image d&apos;aperçu (facultatif, PNG, JPEG ou WebP,{" "}
                            {formatBytes(MAX_PREVIEW_BYTES)} max)
                        </label>
                        <input
                            id="schematic-preview"
                            type="file"
                            accept="image/png,image/jpeg,image/webp"
                            onChange={(e) => {
                                const chosen = e.target.files?.[0] ?? null;
                                setPreview(chosen);
                                setError(previewProblem(chosen));
                            }}
                        />
                        <small>Une capture d&apos;écran de la construction en jeu.</small>
                    </div>

                    {error && <p role="alert">{error}</p>}
                    <div className="offers-header">
                        <button type="submit" className="button" disabled={saving}>
                            {saving ? "Envoi…" : "Déposer"}
                        </button>
                        <Link className="button" to="/schematiques">
                            Annuler
                        </Link>
                    </div>
                </form>
            </div>
        </div>
    );
}
