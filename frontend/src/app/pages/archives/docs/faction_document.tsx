import { useParams } from "react-router-dom";
import DocuLoader from "../../../utils/doc_loader";

type FactionDocLoader = {
    server: string;
    folder: string;
    page: string;
};

function Faction_document() {
    const { server, folder, page } = useParams() as FactionDocLoader;

    if (!server) {
        return (
            <p>
                Invalid document URL, missing server name: {server}/{folder}/
                {page}
            </p>
        );
    } else if (!page) {
        return (
            <p>
                Invalid document URL, missing page name: {server}/{folder}/
                {page}
            </p>
        );
    }

    return <DocuLoader server={server} folder={folder} page={page} />;
}

export default Faction_document;
