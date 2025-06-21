import React from "react";
import ReactDOM from "react-dom/client";
import { HydratedRouter } from "react-router/dom";
import "./index.css";
import { HashRouter } from "react-router-dom";

ReactDOM.hydrateRoot(
    document,
    <React.StrictMode>
        <HashRouter>
            <HydratedRouter />
        </HashRouter>
    </React.StrictMode>
);
