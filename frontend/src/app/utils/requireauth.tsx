import { Navigate, Outlet, useLocation } from "react-router";
import { useAuth } from "./authcontext";

export default function RequireAuth() {
    const auth = useAuth();
    const location = useLocation();

    if (!auth?.token) {
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    return (
        <>
            <Outlet />
        </>
    );
}
