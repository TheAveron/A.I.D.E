import React from 'react';
import ReactDOM from 'react-dom/client';
import {
    createBrowserRouter,
    RouterProvider,
} from "react-router-dom";
import App from './app/App.tsx';
import ErrorPage from './app/components/errors.tsx';
import Home from './app/pages/home.tsx';
import Loi, { loader as rulesLoader } from './app/pages/lois.tsx';
import Map, { loader as mapsLoader } from './app/pages/maps.tsx';
import Rules from './app/pages/ruleslist.tsx';
import Maps from './app/pages/mapslist.tsx'
import './assets/styles/index.css';


const router = createBrowserRouter([
    {
        path: "/A.I.D.E/",
        element: <App />,
        errorElement: <ErrorPage />,
        children: [
            {
                path: "/A.I.D.E",
                element: <Home />
            },
            {
                path: "maps/",
                element: <Maps />,
            },
            {
                path: "rules/",
                element: <Rules />,
            },
            {
                path: "rules/lois/:rulename",
                element: <Loi folder={"lois"}/>,
                loader: rulesLoader,
            },
            {
                path: "rules/marches/:rulename",
                element: <Loi folder={"marches"}/>,
                loader: rulesLoader,
            },
            {
                path: "rules/zones/:rulename",
                element: <Loi folder={"zones"} />,
                loader: rulesLoader,
            },
            {
                path: "maps/:mapname",
                element: <Map />,
                loader: mapsLoader,
            },
        ],
    },
]);

ReactDOM.createRoot(document.getElementById('body')!).render(
    <React.StrictMode>
        <RouterProvider router={router} />
    </React.StrictMode>,
)
