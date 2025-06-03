import {
    createBrowserRouter,
    RouteObject,
} from 'react-router-dom';

import App from './App';
import ErrorPage from './components/errors';
import Home from './pages/home';
import Loi from './pages/rules/rulespages';
import { loader as rulesLoader } from './pages/rules/rulesloader';
import { loader as mapsLoader } from './pages/maps/mapsloader';
import Map from './pages/maps/mapspages';
import Rules from './pages/rules/ruleslist';
import Maps from './pages/maps/mapslist';
import Contribution from './pages/contribution';

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
                path: 'rules/:server/lois/:rulename',
                element: <Loi type="lois" />,
                loader: rulesLoader,
            },
            {
                path: 'rules/:server/marches/:rulename',
                element: <Loi type="marches" />,
                loader: rulesLoader,
            },
            {
                path: 'rules/:server/zones/:rulename',
                element: <Loi type="zones" />,
                loader: rulesLoader,
            },
            {
                path: 'contribution',
                element: <Contribution />,
            },
        ],
    },
];

const router = createBrowserRouter(routes);

export default router;
