import { Link } from "react-router-dom"
import previousArrow from "../../assets/images/previous.svg"

function Rules() {
    return <>
    <button id="previous"><img src={previousArrow} width={"20px"}/><Link to="/A.I.D.E">  Retour</Link></button>
    <section className="text-section">
        <h1>Règlements du realm</h1>

        <h2>A. Lois</h2>

        <ol>
            <li><Link to="lois/territoires">Territoires</Link></li>
            <li><Link to="lois/cites">Cités</Link></li>
            <li><Link to="lois/nations">Nations</Link></li>
        </ol>

        <h2>B. Règlements des différentes zones</h2>

        <ol>
            <li><Link to="zones/spawn">Spawn</Link></li>
            <li><Link to="zones/citadelle_paix">Citadelle de la Paix</Link></li>
            <li><Link to="zones/ursa">URSA</Link></li>
            <li><Link to="zones/alexandrie">Alexandrie</Link></li>
            <li><Link to="zones/arbresagesse">Arbre de la sagesse</Link></li>
        </ol>

        <h2>C. Ventes</h2>

        <p><Link to="marches/index">Vous trouverez ici la liste des choses en vente</Link></p>
    </section>
    </>

}

export default Rules