import { Link } from "react-router-dom";
import MapsArchives from "./maps/maplist";

function Archives() {
    return (
        <section className="text-section">
            <h1>Serveurs anterieurs</h1>
            <h2>Cartes</h2>
            <MapsArchives />
            <h2>Documentations</h2>
            <ul>
                <li>
                    <Link to="documentation/CubeCrusaders">
                        Cube Crusader: The Origin
                    </Link>
                </li>
            </ul>
        </section>
    );
}

export default Archives;
