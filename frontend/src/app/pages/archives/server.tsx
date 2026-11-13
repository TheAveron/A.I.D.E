import PageGenerator from "../../components/pagegen";
import { GoBackButton } from "../../components/buttons/return";
import { getLabelFromFolder } from "../../utils/maps";

function ServerPage(servername: string) {
    return (
        <>
            <div id="map-header" className="column-layout">
                <GoBackButton />
                <div id="map-title">
                    <h2>{getLabelFromFolder(servername)}</h2>
                </div>
            </div>

            {PageGenerator(servername, false)}
        </>
    );
}

export default ServerPage;
