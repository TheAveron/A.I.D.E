import { Link } from "react-router-dom";
import MapsArchives from "./maps/maplist";

import "../../../assets/css/components/section.css";

function Archives() {
    return (
        <section className="text-section">
            <h1>Serveurs anterieurs</h1>
            <h2>Cartes</h2>
            <MapsArchives />
            <h2>Règlements</h2>
            <ul>
                <li>
                    <Link to="/A.I.D.E/archives/rules/">
                        Cube Crusader: The Origin
                    </Link>
                </li>
            </ul>
        </section>
    );
}

export default Archives;
