import "../assets/css/App.css";
import "../assets/css/index.css";
import "../assets/css/components/section.css";
import { Outlet } from "react-router-dom";
import Header from "./components/header";
import Footer from "./components/footer";
import "../assets/css/components/buttons.css";

function App() {
    return (
        <>
            <Header />
            <main>
                <Outlet />
            </main>
            <Footer />
        </>
    );
}

export default App;
