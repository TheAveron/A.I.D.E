import axios from "axios";
import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import MarkdownTable from "../../components/common/markdown_table";
import { getErrorMessage } from "../../utils/apierror";
import { useMe } from "../../hooks/users/me";
import { useRole } from "../../hooks/factions/role";

const TITLE_MIN = 3;
const TITLE_MAX = 200;
const CONTENT_MAX = 100000;

type DocBody = { title: string; content: string };

/**
 * Write a new document of a faction, or edit / delete one of its documents
 * (for the members whose role has manage_docs). The preview is the same
 * Markdown rendering the readers get, minus the document links.
 */
export default function DocumentEditorPage() {
    const { factionid, docname } = useParams();
    const navigate = useNavigate();
    const creating = docname === undefined;

    const { user, loading: userLoading } = useMe();
    const { role, loading: roleLoading } = useRole(user?.role_id ?? null);

    const [title, setTitle] = useState("");
    const [content, setContent] = useState("");
    const [loading, setLoading] = useState(!creating);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    const allowed =
        !!role?.manage_docs &&
        role.faction_id === user?.faction_id &&
        user?.faction_id?.toString() === factionid;

    useEffect(() => {
        if (creating || !factionid || !docname) return;
        const controller = new AbortController();
        axios
            .get<DocBody>(
                `/documents/faction/${encodeURIComponent(factionid)}/${encodeURIComponent(docname)}`,
                { signal: controller.signal },
            )
            .then((res) => {
                setTitle(res.data.title);
                setContent(res.data.content);
                setLoading(false);
            })
            .catch((err) => {
                if (axios.isCancel(err)) return;
                setError(getErrorMessage(err));
                setLoading(false);
            });
        return () => controller.abort();
    }, [creating, factionid, docname]);

    const back = () => navigate(`/faction/${factionid}`);

    const validate = (): string => {
        if (title.trim().length < TITLE_MIN)
            return `Le titre doit faire au moins ${TITLE_MIN} caractères`;
        if (title.length > TITLE_MAX)
            return `Le titre ne peut pas dépasser ${TITLE_MAX} caractères`;
        if (!content.trim()) return "Le contenu est obligatoire";
        if (content.length > CONTENT_MAX) return "Le contenu est trop long";
        return "";
    };

    const save = async (event: FormEvent) => {
        event.preventDefault();
        const problem = validate();
        if (problem) {
            setError(problem);
            return;
        }
        setSaving(true);
        setError("");
        try {
            const body = { title: title.trim(), content };
            if (creating) {
                await axios.post("/documents/create", body);
            } else {
                await axios.put(
                    `/documents/faction/${factionid}/${encodeURIComponent(docname)}`,
                    body,
                );
            }
            back();
        } catch (err) {
            setError(
                axios.isAxiosError(err) && err.response?.status === 409
                    ? "Un document avec ce titre existe déjà."
                    : getErrorMessage(err),
            );
            setSaving(false);
        }
    };

    const remove = async () => {
        if (creating || !window.confirm(`Supprimer « ${title} » ?`)) return;
        setSaving(true);
        setError("");
        try {
            await axios.delete(
                `/documents/faction/${factionid}/${encodeURIComponent(docname)}`,
            );
            back();
        } catch (err) {
            setError(getErrorMessage(err));
            setSaving(false);
        }
    };

    if (userLoading || roleLoading || loading) return <p>Chargement...</p>;

    if (!allowed) {
        return (
            <div className="information-container">
                <p>Vous n'avez pas le droit de modifier les documents.</p>
                <Link to={`/faction/${factionid}`}>Retour à la faction</Link>
            </div>
        );
    }

    return (
        <div className="information-container">
            <div className="snippet-container">
                <h2>
                    {creating ? "Nouveau document" : "Modifier le document"}
                </h2>
                <form onSubmit={save}>
                    <div className="modal-field">
                        <label htmlFor="doc-title">Titre</label>
                        <input
                            id="doc-title"
                            type="text"
                            maxLength={TITLE_MAX}
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                        />
                    </div>
                    <div className="modal-field">
                        <label htmlFor="doc-content">Contenu (Markdown)</label>
                        <textarea
                            id="doc-content"
                            rows={18}
                            maxLength={CONTENT_MAX}
                            style={{ fontFamily: "monospace", width: "100%" }}
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                        />
                    </div>
                    <button type="submit" className="button" disabled={saving}>
                        {saving ? "Enregistrement..." : "Enregistrer"}
                    </button>{" "}
                    <button
                        type="button"
                        className="button"
                        disabled={saving}
                        onClick={back}
                    >
                        Annuler
                    </button>
                    {!creating && (
                        <>
                            {" "}
                            <button
                                type="button"
                                className="button"
                                disabled={saving}
                                onClick={remove}
                            >
                                Supprimer
                            </button>
                        </>
                    )}
                    {error && <p role="alert">{error}</p>}
                </form>
            </div>
            <div className="snippet-container">
                <h2>Aperçu</h2>
                <section className="text-section">
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{ table: MarkdownTable }}
                    >
                        {`# ${title}\n\n${content}`}
                    </ReactMarkdown>
                </section>
            </div>
        </div>
    );
}
