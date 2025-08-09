// AuthProvider.tsx
import axios from "axios";
import {
    createContext,
    useContext,
    useEffect,
    useMemo,
    useState,
    type ReactNode,
} from "react";

import { useNavigate } from "react-router-dom";
import { jwtDecode } from "jwt-decode";

// --- Types ---
interface AuthContextType {
    token: string | null;
    setToken: React.Dispatch<React.SetStateAction<string | null>>;
}

interface DecodedToken {
    exp: number;
    [key: string]: unknown;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [token, setToken] = useState<string | null>(() => {
        if (typeof window !== "undefined") {
            return localStorage.getItem("token");
        }
        return null;
    });

    useEffect(() => {
        let logoutTimer: number;

        if (token) {
            try {
                const decoded = jwtDecode<DecodedToken>(token);

                if (!decoded.exp) {
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
                    localStorage.setItem("token", token);
                }
            } catch (error) {
                console.error("Invalid token", error);
                setToken(null);
            }
        } else {
            delete axios.defaults.headers.common["Authorization"];
            localStorage.removeItem("token");
        }

        return () => {
            if (logoutTimer) clearTimeout(logoutTimer);
        };
    }, [token]);

    const navigate = useNavigate();

    const handleLogout = (sessionExpired = false) => {
        setToken(null);
        if (sessionExpired) {
            navigate("A.I.D.E/login", {
                state: { message: "Session expired, please log in again." },
                replace: true,
            });
        } else {
            navigate("A.I.D.E/login", { replace: true });
        }
    };

    const contextValue = useMemo(() => ({ token, setToken }), [token]);

    return (
        <AuthContext.Provider value={contextValue}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
};

export default AuthProvider;
