import { Link } from "react-router-dom";
import "../../assets/css/components/header.css";
import { useAuth } from "../utils/authprovider";

function Header() {
    console.log("e");
    console.log(useAuth());
    const { token } = useAuth() ?? {};

    return (
        <header id="header">
            <Link to="/A.I.D.E" className="title link">
                Cube Crusader
            </Link>
            <nav>
                <Link className="link" to="/A.I.D.E/actual">
                    Map
                </Link>
                <Link className="link" to="/A.I.D.E/archives">
                    Archives
                </Link>
                <Link className="link" to="/A.I.D.E/contribuer">
                    Contribute
                </Link>

                {token ? (
                    <Link className="link" to="/A.I.D.E/profile">
                        Profile
                    </Link>
                ) : (
                    <Link className="button" id="signin" to="/A.I.D.E/login">
                        Sign in
                    </Link>
                )}
            </nav>
        </header>
    );
}

export default Header;
