import { Outlet } from "react-router-dom";
import Header from "./components/header";
import Footer from "./components/footer";
import AuthProvider from "./utils/authprovider";

import "../assets/css/App.css";
import "../assets/css/index.css";

function App() {
    return (
        <AuthProvider>
            <Header />
            <main id="main">
                <Outlet />
            </main>
            <Footer />
        </AuthProvider>
    );
}

export default App;
