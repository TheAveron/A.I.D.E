import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "./authprovider";

export default function RequireAuth() {
    const auth = useAuth();
    const location = useLocation();

    if (!auth?.token) {
        return (
            <Navigate to="/A.I.D.E/login" state={{ from: location }} replace />
        );
    }

    return (
        <>
            <Outlet />
        </>
    );
}
