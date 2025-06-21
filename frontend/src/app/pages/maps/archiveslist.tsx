import { Link } from "react-router-dom";

const mapFolders = [
    "OCube_crusader",
    "OLSLN",
    "OLSPLW_zoom",
    "OStrong_world_zoom",
    "OSurvival_islands_zoom",
    "OUtopia_zoom",
    "EUtopia_zoom",
];

const getLabelFromFolder = (folder: string) => {
    const mapping: Record<string, string> = {
        OCube_crusader: "Map de Cube Crusader",
        OLSLN: "Map de la survie pour les nuls",
        OLSPLW_zoom: "Map de la survie pour les Wariors",
        OStrong_world_zoom: "Map de Strong World",
        OSurvival_islands_zoom: "Map de Survival Islands",
        OUtopia_zoom: "Map de l'overworld d'Utopia",
        EUtopia_zoom: "Map de l'end d'Utopia",
    };

    return mapping[folder] || folder;
};

function Maps() {
    return (
        <section className="text-section">
            <h1>Liste des maps consultables</h1>
            <ul>
                {mapFolders.map((folder) => (
                    <li key={folder}>
                        <Link to={folder}>{getLabelFromFolder(folder)}</Link>
                    </li>
                ))}
            </ul>
        </section>
    );
}

export default Maps;
