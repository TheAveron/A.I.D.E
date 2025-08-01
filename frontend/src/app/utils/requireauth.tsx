import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./authprovider";

export function RequireAuth({ children }: { children: React.ReactNode }) {
    const auth = useAuth();
    const location = useLocation();

    console.log(auth);

    // If no token → redirect to login page
    if (!auth?.token) {
        return (
            <Navigate to="/A.I.D.E/login" state={{ from: location }} replace />
        );
    }

    // If logged in → show the protected content
    return <>{children}</>;
}
