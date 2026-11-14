import { Link } from "react-router";

import { useFactionDocuments } from "../hooks/documents";
import { useMe } from "../hooks/me";
import { useRole } from "../hooks/role";
import { NewDocument } from "../buttons/newdoc";

/** The documents of a faction; its members who manage docs can add some. */
export default function FactionDocuments({ factionId }: { factionId: string }) {
    const { documents, loading, error, refresh } =
        useFactionDocuments(factionId);
    const { user } = useMe();
    const { role } = useRole(user?.role_id ?? null);

    // Same rule as the API: documents are written in one's own faction
    const canWrite =
        !!role?.manage_docs && user?.faction_id === Number(factionId);

    return (
        <div className="snippet-container">
            <h2>Documents</h2>
            {canWrite && <NewDocument onCreated={refresh} />}
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
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
