import { useParams } from "react-router";
import DocuLoader from "../../utils/doc_loader";

/** A page of the current server's documentation (Age of Steam). */
function AosDocument() {
    const { page = "index" } = useParams();

    return (
        <DocuLoader
            url={`/documents/aos/${encodeURIComponent(page)}`}
            linkBase="/documentation/AgeOfSteam/"
        />
    );
}

export default AosDocument;
