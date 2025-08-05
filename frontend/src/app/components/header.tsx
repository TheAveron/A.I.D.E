import { Link } from "react-router-dom";
import { useAuth } from "../utils/authprovider";

import "../../assets/css/components/header.css";
import "../../assets/css/components/buttons.css";

function Header() {
    const { token } = useAuth() ?? {};

    return (
        <header id="header">
            <Link to="/A.I.D.E" className="title link">
                Cube Crusader
            </Link>
            <nav>
                <Link className="link" to="/A.I.D.E/actual">
                    Carte
                </Link>

                {token ? (
                    <>
                        <Link className="link" to="/A.I.D.E/factions">
                            Factions
                        </Link>
                        <Link className="link" to="/A.I.D.E/offers">
                            Offres
                        </Link>

                        <Link className="link" to="/A.I.D.E/contribuer">
                            Contribuer
                        </Link>
                        <Link className="link" to="/A.I.D.E/profile">
                            Profile
                        </Link>
                    </>
                ) : (
                    <>
                        <Link className="link" to="/A.I.D.E/archives">
                            Archives
                        </Link>
                        <Link
                            className="button"
                            id="signin"
                            to="/A.I.D.E/login"
                        >
                            Connection
                        </Link>
                    </>
                )}
            </nav>
        </header>
    );
}

export default Header;
