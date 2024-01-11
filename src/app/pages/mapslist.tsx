import { Link } from "react-router-dom";
import previousArrow from "../../assets/images/previous.svg";

function Maps() {
    return <>
        <button id="previous"><img src={previousArrow} width={"20px"} /><Link to="/">  Retour</Link></button>
        <section className="text-section">
            <h1>Liste des maps consultables</h1>
            <ul>
                <li><Link to="OCube_crusader">Map de Cube Crusader</Link></li>
                <li><Link to="OLSLN">Map de la survie pour les nuls</Link></li>
                <li><Link to="OLSPLW_zoom">Map de la survie pour les Wariors</Link></li>
                <li><Link to="OStrong_world_zoom">Map de Strong World</Link></li>
                <li><Link to="OSurvival_islands_zoom">Map de Survival Islands</Link></li>
                <li><Link to="OUtopia_zoom">Map de l'overworld d'Utopia</Link></li>
                <li><Link to="EUtopia_zoom">Map de l'end d'Utopia</Link></li>
            </ul>
        </section>

    </>
}

export default Maps