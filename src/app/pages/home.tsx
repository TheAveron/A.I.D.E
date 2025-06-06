import { Link } from "react-router-dom"

function Home() {
    return <section className="text-section">
        <h1>Bienvenue sur le site du realm Cube Crusader !</h1>
        <p>Vous trouverez ici plein d'informations relatives à l'organisation du Realm ainsi que les différentes maps associées aux realms passés</p>
        <ul>
            <li>Vous trouverez <Link to="/A.I.D.E/rules">ici</Link> les différents règlements.</li>
            <li>Vous trouverez <Link to="/A.I.D.E/maps">ici</Link> la liste des maps visualiables en ligne.</li>
        </ul>
    </section>
}

export default Home