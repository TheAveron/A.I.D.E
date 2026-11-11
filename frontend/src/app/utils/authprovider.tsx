// AuthProvider.tsx
import axios from "axios";
import {
    useCallback,
    useEffect,
    useMemo,
    useState,
    type ReactNode,
} from "react";

import { useNavigate } from "react-router";
import { jwtDecode } from "jwt-decode";
import { AuthContext } from "./authcontext";

// --- Types ---
interface DecodedToken {
    exp: number;
    [key: string]: unknown;
}

const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [token, setToken] = useState<string | null>(() => {
        if (typeof window !== "undefined") {
            return sessionStorage.getItem("token");
        }
        return null;
    });

    const navigate = useNavigate();

    const handleLogout = useCallback(
        (sessionExpired = false) => {
            setToken(null);
            if (sessionExpired) {
                navigate("/login", {
                    state: { message: "Session expired, please log in again." },
                    replace: true,
                });
            } else {
                navigate("/login", { replace: true });
            }
        },
        [navigate],
    );

    useEffect(() => {
        let logoutTimer: number;

        if (token) {
            try {
                const decoded = jwtDecode<DecodedToken>(token);

                if (!Number.isFinite(decoded.exp) || decoded.exp <= 0) {
                    console.warn("Token does not contain an expiration claim");
                    setToken(null);
                    return;
                }

                const expiryTime = decoded.exp * 1000; // convert seconds → ms
                const timeUntilExpiry = expiryTime - Date.now() - 5000; // 5s safety margin

                if (timeUntilExpiry <= 0) {
                    handleLogout();
                } else {
                    logoutTimer = setTimeout(() => {
                        handleLogout(true);
                    }, timeUntilExpiry);

                    axios.defaults.headers.common["Authorization"] =
                        `Bearer ${token}`;
                    sessionStorage.setItem("token", token);
                }
            } catch (error) {
                console.error("Invalid token", error);
                setToken(null);
            }
        } else {
            delete axios.defaults.headers.common["Authorization"];
            sessionStorage.removeItem("token");
        }

        return () => {
            if (logoutTimer) clearTimeout(logoutTimer);
        };
    }, [token, handleLogout]);

    const contextValue = useMemo(() => ({ token, setToken }), [token]);

    return (
        <AuthContext.Provider value={contextValue}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthProvider;
