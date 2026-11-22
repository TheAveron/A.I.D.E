import { useParams } from "react-router";
import DocuLoader from "../../../utils/doc_loader";

/** A document of a former server (read only, like all the archives). */
function Document() {
    const { server, page } = useParams();

    if (!server || !page) {
        return (
            <p>
                Invalid document URL: {server}/{page}
            </p>
        );
    }

    return (
        <DocuLoader
            url={`/documents/archives/${encodeURIComponent(server)}/${encodeURIComponent(page)}`}
            linkBase="/archives/documentation/"
        />
    );
}

export default Document;
