import { Link } from "react-router-dom"
import "../../assets/styles/header.css"
import ThemeChoice from "../utils/theme"

function Header() {
    return (
        <header>
            <div className="title"><Link to={"/A.I.D.E"}>Cube Crusader</Link></div>
            <nav className="navbar">
                <Link to={"/A.I.D.E/maps"}>Maps</Link>
                <Link to={"/A.I.D.E/rules"}>Rules</Link>
                <Link to={"/A.I.D.E/contribution"}>Contribuer</Link>
                <ThemeChoice />
            </nav>
        </header>
    )
}

export default Header