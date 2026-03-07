import { useParams } from "react-router-dom";
import DocuLoader from "../../../utils/doc_loader";

type DocumentLoader = {
    server: string;
    page: string;
};

function Document() {
    const { server, page } = useParams() as DocumentLoader;

    if (!server) {
        return (
            <p>
                Invalid document URL, missing server name: {server}/{page}
            </p>
        );
    } else if (!page) {
        return (
            <p>
                Invalid document URL, missing page name: {server}/{page}
            </p>
        );
    }

    return <DocuLoader server={server} page={page} />;
}

export default Document;
