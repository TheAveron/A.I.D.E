import axios from "axios";
import { jwtDecode } from "jwt-decode";

const EXPIRY_MARGIN_MS = 5000;

/** Whether `token` is a decodable JWT that is not about to expire. */
export function isTokenUsable(token: string): boolean {
    try {
        const { exp } = jwtDecode<{ exp?: number }>(token);
        return (
            typeof exp === "number" &&
            Number.isFinite(exp) &&
            exp * 1000 - Date.now() > EXPIRY_MARGIN_MS
        );
    } catch {
        return false;
    }
}

/**
 * Make every axios request carry `token` (or none).
 *
 * This must run synchronously, not from an effect: React runs a child's
 * effects before its parent's, so a page whose hook fetches on mount would
 * otherwise fire its request before the provider had set the header (a 401 on
 * every page reload).
 */
export function applyAuthHeader(token: string | null): void {
    if (token && isTokenUsable(token)) {
        axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    } else {
        delete axios.defaults.headers.common["Authorization"];
    }
}
