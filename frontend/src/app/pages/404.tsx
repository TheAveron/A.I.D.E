import logo from "../../assets/images/Error.png";

import { GoBackButton } from "../components/buttons/return";

import "../../assets/css/components/section.css";
import "../../assets/css/pages/404.css";
import "../../assets/css/components/buttons.css";

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
                <GoBackButton label="Accueil" />
            </section>
        </div>
    );
}

export default Error404;
