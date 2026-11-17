import { Outlet } from "react-router";
import Header from "./components/layout/header";
import Footer from "./components/layout/footer";
import AuthProvider from "./utils/authprovider";

import "../assets/css/styles.css";

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
