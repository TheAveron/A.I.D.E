import "../assets/css/App.css";
import "../assets/css/index.css";
import "../assets/css/components/section.css";
import { Outlet } from "react-router-dom";
import Header from "./components/header";
import Footer from "./components/footer";
import "../assets/css/components/buttons.css";

import "../assets/css/pages/archives.css";

function App() {
    return (
        <>
            <Header />
            <main id="main">
                <Outlet />
            </main>
            <Footer />
        </>
    );
}

export default App;
