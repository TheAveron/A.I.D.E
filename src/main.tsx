import React from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';
import router from './app/router.tsx';
import './assets/styles/index.css';

ReactDOM.createRoot(document.getElementById('body')!).render(
    <React.StrictMode>
        <RouterProvider router={router} />
    </React.StrictMode>
);
