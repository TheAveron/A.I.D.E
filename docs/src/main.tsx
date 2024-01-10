import React from 'react'
import ReactDOM from 'react-dom/client'
import {
    createBrowserRouter,
    RouterProvider,
} from "react-router-dom";
import App from './app/App.tsx'
import './assets/styles/index.css'
import ErrorPage from './app/components/errors.tsx';
import Map from './app/pages/maps.tsx';
import Rules from './app/pages/rules.tsx';
import Home from './app/pages/home.tsx';
import Loi from './app/pages/lois.tsx';
import { loader as markdownLoader } from './app/pages/lois.tsx';


const router = createBrowserRouter([
    {
        path: "/",
        element: <App />,
        errorElement: <ErrorPage />,
        children: [
            {
                path: "/",
                element: <Home />
            },
            {
                path: "maps/:mapid",
                element: <Map />,
            },
            {
                path: "rules/",
                element: <Rules />,
            },
            {
                path: "rules/lois/:rulename",
                element: <Loi folder={"lois"}/>,
                loader: markdownLoader,
            },
            {
                path: "rules/marches/:rulename",
                element: <Loi folder={"marches"}/>,
                loader: markdownLoader,
            },{
                path: "rules/zones/:rulename",
                element: <Loi folder={"zones"} />,
                loader: markdownLoader,
            },
        ],
    },
]);

ReactDOM.createRoot(document.getElementById('body')!).render(
    <React.StrictMode>
        <RouterProvider router={router} />
    </React.StrictMode>,
)
