import {
    createBrowserRouter,
    RouteObject,
} from 'react-router-dom';

import App from './App';
import ErrorPage from './components/errors';
import Home from './pages/home';
import Loi, { loader as rulesLoader } from './pages/lois';
import Map, { loader as mapsLoader } from './pages/maps';
import Rules from './pages/ruleslist';
import Maps from './pages/mapslist';

const routes: RouteObject[] = [
    {
        path: '/A.I.D.E/',
        element: <App />,
        errorElement: <ErrorPage />,
        children: [
            {
                index: true,
                element: <Home />,
            },
            {
                path: 'maps',
                element: <Maps />,
            },
            {
                path: 'maps/:mapname',
                element: <Map />,
                loader: mapsLoader,
            },
            {
                path: 'rules',
                element: <Rules />,
            },
            {
                path: 'rules/lois/:rulename',
                element: <Loi folder="lois" />,
                loader: rulesLoader,
            },
            {
                path: 'rules/marches/:rulename',
                element: <Loi folder="marches" />,
                loader: rulesLoader,
            },
            {
                path: 'rules/zones/:rulename',
                element: <Loi folder="zones" />,
                loader: rulesLoader,
            },
        ],
    },
];

export default createBrowserRouter(routes);
