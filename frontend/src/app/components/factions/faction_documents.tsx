import { Link } from "react-router";

import { useFactionDocuments } from "../../hooks/factions/documents";
import { useMe } from "../../hooks/users/me";
import { useRole } from "../../hooks/factions/role";
import axios from "axios";
import { getErrorMessage } from "../../utils/apierror";
import { useState } from "react";

/** The documents of a faction; its members who manage docs can add some. */
export default function FactionDocuments({ factionId }: { factionId: string }) {
    const { documents, loading, error, refresh } =
        useFactionDocuments(factionId);
    const { user } = useMe();
    const { role } = useRole(user?.role_id ?? null);

    // Same rule as the API: documents are written in one's own faction
    const [deleteError, setDeleteError] = useState<string | null>(null);

    const remove = async (docName: string, title: string) => {
        if (!window.confirm(`Supprimer « ${title} » ?`)) return;
        setDeleteError(null);
        try {
            await axios.delete(
                `/documents/faction/${factionId}/${encodeURIComponent(docName)}`,
            );
            refresh();
        } catch (err) {
            setDeleteError(getErrorMessage(err));
        }
    };

    const canWrite =
        !!role?.manage_docs && user?.faction_id === Number(factionId);

    return (
        <div className="snippet-container">
            <h2>Documents</h2>
            {canWrite && (
                <Link
                    className="button"
                    to={`/faction/${factionId}/documents/new`}
                >
                    Nouveau document
                </Link>
            )}
            {deleteError && <p role="alert">{deleteError}</p>}
            {error && <p role="alert">{error}</p>}
            {loading ? (
                <p>Chargement des documents...</p>
            ) : documents.length === 0 ? (
                <p className="empty-state">Aucun document.</p>
            ) : (
                <ul>
                    {documents.map((doc) => (
                        <li key={doc.doc_name}>
                            <Link
                                to={`/archives/documentation/${encodeURIComponent(doc.server)}/${encodeURIComponent(doc.folder)}/${encodeURIComponent(doc.doc_name)}`}
                            >
                                {doc.title}
                            </Link>
                            {canWrite && (
                                <>
                                    {" "}
                                    <Link
                                        to={`/faction/${factionId}/documents/${encodeURIComponent(doc.doc_name)}/edit`}
                                    >
                                        Modifier
                                    </Link>{" "}
                                    <button
                                        type="button"
                                        className="button"
                                        onClick={() =>
                                            remove(doc.doc_name, doc.title)
                                        }
                                    >
                                        Supprimer
                                    </button>
                                </>
                            )}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
