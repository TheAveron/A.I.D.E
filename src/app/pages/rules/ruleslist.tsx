import { Link } from "react-router-dom"
import { GoBackButton } from "../../components/goback_button"

function Rules() {
    return <>
        <GoBackButton />
        <section className="text-section">
            <h1>Règlements du realm</h1>

            <h2>A. Lois</h2>

            <ol>
                <li><Link to="CubeCrusaders/lois/territoires">Territoires</Link></li>
                <li><Link to="CubeCrusaders/lois/cites">Cités</Link></li>
                <li><Link to="CubeCrusaders/lois/nations">Nations</Link></li>
            </ol>

            <h2>B. Règlements des différentes zones</h2>

            <ol>
                <li><Link to="CubeCrusaders/zones/spawn">Spawn</Link></li>
                <li><Link to="CubeCrusaders/zones/citadelle_paix">Citadelle de la Paix</Link></li>
                <li><Link to="CubeCrusaders/zones/ursa">URSA</Link></li>
                <li><Link to="CubeCrusaders/zones/alexandrie">Alexandrie</Link></li>
                <li><Link to="CubeCrusaders/zones/arbresagesse">Arbre de la sagesse</Link></li>
            </ol>

            <h2>C. Ventes</h2>

            <p><Link to="CubeCrusaders/marches/index">Vous trouverez ici la liste des choses en vente</Link></p>
        </section>
    </>
}

export default Rules