import { Outlet } from "react-router";
import Header from "./components/layout/header";
import Footer from "./components/layout/footer";
import SectionTabs from "./components/layout/section_tabs";
import AuthProvider from "./utils/authprovider";

import "../assets/css/styles.css";

function App() {
    return (
        <AuthProvider>
            <Header />
            <main id="main">
                <SectionTabs />
                <Outlet />
            </main>
            <Footer />
        </AuthProvider>
    );
}

export default App;
