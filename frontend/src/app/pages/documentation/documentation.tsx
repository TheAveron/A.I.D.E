import { Link } from "react-router";

import { useAllFactionDocuments } from "../../hooks/documents/all_faction_documents";

/**
 * The current server's documentation: its own pages, and the documents every
 * faction has written (public, like reading them).
 */
export default function DocumentationPage() {
    const { factions, loading, error, retry } = useAllFactionDocuments();

    return (
        <section className="text-section">
            <h1>Documentation d&apos;Age of Steam</h1>
            <ul>
                <li>
                    <Link to="/documentation/AgeOfSteam">
                        Présentation du serveur
                    </Link>
                </li>
            </ul>

            <h2>Documents des factions</h2>
            {error ? (
                <>
                    <p role="alert">{error}</p>
                    <button type="button" className="button" onClick={retry}>
                        Réessayer
                    </button>
                </>
            ) : loading ? (
                <p>Chargement des documents...</p>
            ) : factions.length === 0 ? (
                <p className="empty-state">
                    Aucune faction n&apos;a encore publié de document.
                </p>
            ) : (
                factions.map((faction) => (
                    <div key={faction.faction_id}>
                        <h3>{faction.faction_name}</h3>
                        <ul>
                            {faction.documents.map((doc) => (
                                <li key={doc.doc_name}>
                                    <Link
                                        to={`/faction/${faction.faction_id}/documents/${encodeURIComponent(doc.doc_name)}`}
                                    >
                                        {doc.title}
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    </div>
                ))
            )}
        </section>
    );
}
