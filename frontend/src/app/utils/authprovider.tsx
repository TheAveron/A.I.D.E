// AuthProvider.tsx
import axios from "axios";
import {
    useCallback,
    useEffect,
    useMemo,
    useRef,
    useState,
    type ReactNode,
} from "react";

import { useNavigate } from "react-router";
import { jwtDecode } from "jwt-decode";
import { applyAuthHeader } from "./authheader";
import { AuthContext } from "./authcontext";

// --- Types ---
interface DecodedToken {
    exp: number;
    [key: string]: unknown;
}

/** The token's expiry (seconds since the epoch), or null if it has none. */
function tokenExpiry(token: string | null): number | null {
    if (!token) return null;
    try {
        const { exp } = jwtDecode<DecodedToken>(token);
        if (Number.isFinite(exp) && exp > 0) return exp;
        console.warn("Token does not contain an expiration claim");
    } catch (error) {
        console.error("Invalid token", error);
    }
    return null;
}

const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [token, setToken] = useState<string | null>(() => {
        if (typeof window === "undefined") return null;

        const stored = sessionStorage.getItem("token");
        // Set the header now, during the first render: the effect below runs
        // after the children's effects, which would already have fetched
        // without it (see applyAuthHeader).
        applyAuthHeader(stored);
        return stored;
    });

    const navigate = useNavigate();

    const handleLogout = useCallback(
        (sessionExpired = false) => {
            setToken(null);
            if (sessionExpired) {
                navigate("/login", {
                    state: {
                        message: "Session expirée, veuillez vous reconnecter.",
                    },
                    replace: true,
                });
            } else {
                navigate("/login", { replace: true });
            }
        },
        [navigate],
    );

    // The "Déconnexion" button: same as an expired session, without the notice.
    const logout = useCallback(() => {
        applyAuthHeader(null);
        handleLogout(false);
    }, [handleLogout]);

    // An unreadable token, or one without an expiry, counts as no token:
    // derived here rather than reset to null from the effect below.
    const expiry = useMemo(() => tokenExpiry(token), [token]);
    const validToken = expiry === null ? null : token;

    useEffect(() => {
        let logoutTimer: number;

        if (validToken && expiry !== null) {
            const expiryTime = expiry * 1000; // convert seconds → ms
            const timeUntilExpiry = expiryTime - Date.now() - 5000; // 5s safety margin

            // Already expired: logged out right away, through the same timer
            // (a callback, not a state change in the effect's body).
            logoutTimer = setTimeout(
                () => handleLogout(true),
                Math.max(0, timeUntilExpiry),
            );

            if (timeUntilExpiry > 0) {
                axios.defaults.headers.common["Authorization"] =
                    `Bearer ${validToken}`;
                sessionStorage.setItem("token", validToken);
            }
        } else {
            delete axios.defaults.headers.common["Authorization"];
            sessionStorage.removeItem("token");
        }

        return () => {
            if (logoutTimer) clearTimeout(logoutTimer);
        };
    }, [validToken, expiry, handleLogout]);

    const currentToken = useRef(validToken);
    useEffect(() => {
        currentToken.current = validToken;
    }, [validToken]);

    useEffect(() => {
        const id = axios.interceptors.response.use(
            (response) => response,
            (error: unknown) => {
                if (
                    axios.isAxiosError(error) &&
                    error.response?.status === 401 &&
                    currentToken.current &&
                    error.config?.headers?.Authorization ===
                        `Bearer ${currentToken.current}`
                ) {
                    handleLogout(true);
                }
                return Promise.reject(error);
            },
        );
        return () => axios.interceptors.response.eject(id);
    }, [handleLogout]);

    const contextValue = useMemo(
        () => ({ token: validToken, setToken, logout }),
        [validToken, logout],
    );

    return (
        <AuthContext.Provider value={contextValue}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthProvider;
