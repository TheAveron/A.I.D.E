import logo from "../../assets/images/Error.png";
import "../../assets/css/pages/404.css";
import { Link } from "react-router-dom";

function Error404() {
    return (
        <div className="content">
            <section id="error">
                <img
                    alt="Minecraft"
                    id="credits-logo"
                    src={logo}
                    style={{ width: "40vw" }}
                />
                <p>
                    Oops, il semblerait que la page que vous cherchiez n'existe
                    pas
                </p>
                <Link className="button" to="/A.I.D.E">
                    Retour au menu
                </Link>
            </section>
        </div>
    );
}

export default Error404;
