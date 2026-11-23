import { Link } from "react-router";

import { useAuth } from "../utils/authcontext";
import { NAV_SECTIONS, visibleItems } from "../utils/navigation";

/** What each section is for, in one line. */
const SECTION_INTROS: Record<string, string> = {
    economie: "Les factions, leurs monnaies et les échanges entre joueurs.",
    reseau: "Le chemin de fer : plan, lignes, gares et trains.",
    ressources: "La documentation du serveur, les schematics et les archives.",
};

/** The home page: a word of welcome and a map of the site. */
function Home() {
    const { token } = useAuth();
    const loggedIn = !!token;

    return (
        <div className="information-container">
            <div className="snippet-container home-intro">
                <h2>Bienvenue sur Cube Crusader : Age of Steam</h2>
                <p>
                    Ce site accompagne le serveur : la carte en direct, la
                    gestion des factions et du marché, le réseau ferré et toute
                    la documentation.{" "}
                    {loggedIn ? null : (
                        <>
                            <Link to="/login">Connectez-vous</Link> pour accéder
                            à toutes les pages.
                        </>
                    )}
                </p>
                <Link className="button" to="/actual">
                    Ouvrir la carte
                </Link>
            </div>

            {NAV_SECTIONS.map((section) => {
                const items = visibleItems(section, loggedIn);
                if (items.length === 0) return null;
                return (
                    <div key={section.id} className="snippet-container home-section">
                        <h2>{section.label}</h2>
                        <p>{SECTION_INTROS[section.id]}</p>
                        <ul>
                            {items.map((item) => (
                                <li key={item.to}>
                                    <Link to={item.to}>{item.label}</Link>
                                </li>
                            ))}
                        </ul>
                    </div>
                );
            })}
        </div>
    );
}

export default Home;
