import PageGenerator from "../../components/pagegen";
import { GoBackButton } from "../../components/buttons/return";

import "../../../assets/css/pages/archives.css";

const getLabelFromFolder = (folder: string) => {
    const mapping: Record<string, string> = {
        OCube_crusader: "Cube Crusader",
        OLSLN: "La survie pour les nuls",
        OLSPLW_zoom: "La survie pour les Wariors",
        OStrong_world_zoom: "Strong World",
        OSurvival_islands_zoom: "Survival Islands",
        OUtopia_zoom: "Utopia",
        AOS: "Age of Steam",
    };

    return mapping[folder] || folder;
};

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
