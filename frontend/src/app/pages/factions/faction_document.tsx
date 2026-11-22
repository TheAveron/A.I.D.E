import { useParams } from "react-router";
import DocuLoader from "../../utils/doc_loader";

/** A document written by a faction of the current server. */
export default function FactionDocumentPage() {
    const { factionid, docname } = useParams();

    if (!factionid || !docname) {
        return <p>Document introuvable.</p>;
    }

    return (
        <DocuLoader
            url={`/documents/faction/${encodeURIComponent(factionid)}/${encodeURIComponent(docname)}`}
            linkBase={`/faction/${encodeURIComponent(factionid)}/documents/`}
            withTitle
        />
    );
}
