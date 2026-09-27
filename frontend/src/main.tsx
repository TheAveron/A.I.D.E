import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter, HydratedRouter } from "react-router";

ReactDOM.hydrateRoot(
    document.getElementById("root")!,
    <React.StrictMode>
        <HashRouter>
            <HydratedRouter />
        </HashRouter>
    </React.StrictMode>,
);
