import { Link } from "react-router";

import { LISTED_MAPS, getLabelFromFolder } from "../../../utils/maps";

function MapsArchives() {
    return (
        <ul>
            {LISTED_MAPS.map((folder) => (
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
