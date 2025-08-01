import React from "react";
import ReactDOM from "react-dom/client";
import { HydratedRouter } from "react-router/dom";
import { HashRouter } from "react-router-dom";
import "./index.css";
import AuthProvider from "./app/utils/authprovider";

ReactDOM.hydrateRoot(
    document,
    <React.StrictMode>
        <HashRouter>
            <AuthProvider>
                <HydratedRouter />
            </AuthProvider>
        </HashRouter>
    </React.StrictMode>
);
