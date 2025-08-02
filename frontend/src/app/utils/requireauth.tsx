import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "./authprovider";

export default function RequireAuth() {
    const auth = useAuth();
    const location = useLocation();

    console.log("e");

    console.log(auth.token);

    // If no token → redirect to login page
    if (!auth?.token) {
        return (
            <Navigate to="/A.I.D.E/login" state={{ from: location }} replace />
        );
    }

    // If logged in → show the protected content
    return (
        <>
            <Outlet />
        </>
    );
}
