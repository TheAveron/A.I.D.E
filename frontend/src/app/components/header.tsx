import { Link } from "react-router";

import { useAuth } from "../utils/authcontext";

function Header() {
    const { token } = useAuth() ?? {};

    return (
        <header id="header">
            <Link to="" className="title link">
                Cube Crusader
            </Link>
            <nav>
                <Link className="link" to="/actual">
                    Carte
                </Link>
                <Link className="link" to="/documentation/AgeOfSteam">
                    Documentation
                </Link>

                {token ? (
                    <>
                        <Link className="link" to="/factions">
                            Factions
                        </Link>
                        <Link className="link" to="/offers">
                            Offres
                        </Link>
                        <Link className="link" to="/contribuer">
                            Contribuer
                        </Link>
                        <Link className="link" to="/profile">
                            Profil
                        </Link>
                    </>
                ) : (
                    <>
                        <Link className="link" to="/archives">
                            Archives
                        </Link>
                        <Link className="button" id="signin" to="/login">
                            Connexion
                        </Link>
                    </>
                )}
            </nav>
        </header>
    );
}

export default Header;
