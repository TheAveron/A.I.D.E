import { Link } from "react-router-dom"
import "../../assets/styles/header.css"
import ThemeChoice from "../utils/theme"

function Header() {
    return (
        <header>
            <div className="title"><Link to={"/"}>Cube Crusader</Link></div>
            <nav className="navbar"><Link to={"credit"}>Credit</Link><ThemeChoice /></nav>
        </header>
    )
}

export default Header