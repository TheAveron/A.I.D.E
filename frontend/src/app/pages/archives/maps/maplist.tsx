import { Link } from "react-router-dom";

const mapFolders = [
    "OCube_crusader",
    "OLSLN",
    "OLSPLW_zoom",
    "OStrong_world_zoom",
    "OSurvival_islands_zoom",
    "OUtopia_zoom",
    "EUtopia_zoom",
    "OAOS_zoom",
];

const getLabelFromFolder = (folder: string) => {
    const mapping: Record<string, string> = {
        OAOS_zoom: "Cube Crusader: Age of Steam",
        OCube_crusader: "Cube Crusader: The Origin",
        OLSLN: "La survie pour les nuls",
        OLSPLW_zoom: "La survie pour les Wariors",
        OStrong_world_zoom: "Strong World",
        OSurvival_islands_zoom: "Survival Islands",
        OUtopia_zoom: "Utopia",
        EUtopia_zoom: "End d'Utopia",
    };

    return mapping[folder] || folder;
};

function MapsArchives() {
    return (
        <ul>
            {mapFolders.map((folder) => (
                <li key={folder}>
                    <Link to={"maps/" + folder}>
                        {getLabelFromFolder(folder)}
                    </Link>
                </li>
            ))}
        </ul>
    );
}

export default MapsArchives;
