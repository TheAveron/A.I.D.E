import { useParams } from "react-router";
import DocuLoader from "../../../utils/doc_loader";

/** A document of a former server kept in a sub-folder (lois/, zones/...). */
function FolderDocument() {
    const { server, folder, page } = useParams();

    if (!server || !folder || !page) {
        return (
            <p>
                Invalid document URL: {server}/{folder}/{page}
            </p>
        );
    }

    return (
        <DocuLoader
            url={`/documents/archives/${encodeURIComponent(server)}/${encodeURIComponent(folder)}/${encodeURIComponent(page)}`}
            linkBase="/archives/documentation/"
        />
    );
}

export default FolderDocument;
