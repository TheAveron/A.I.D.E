import React from "react";
import ReactDOM from "react-dom/client";
import { HydratedRouter } from "react-router-dom";
import { HashRouter } from "react-router-dom";

ReactDOM.hydrateRoot(
    document.getElementById("root")!,
    <React.StrictMode>
        <HashRouter>
            <HydratedRouter />
        </HashRouter>
    </React.StrictMode>
);
