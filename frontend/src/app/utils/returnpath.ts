const HOME = "/";

// Pages that would send a logged-in user straight back to where they are.
const AUTH_PAGES = ["/login", "/register"];

/**
 * Where to go after logging in: the page the user was sent away from
 * (`state.from`, set by RequireAuth), or the home page.
 *
 * The path must stay inside the application: it has to start with a single
 * "/" (not "//host", not a relative path) and must not be a login page.
 */
export function getSafeReturnPath(state: unknown): string {
    if (!state || typeof state !== "object" || !("from" in state)) return HOME;

    const from = state.from as {
        pathname?: unknown;
        search?: unknown;
        hash?: unknown;
    } | null;

    if (!from || typeof from !== "object") return HOME;

    const { pathname, search, hash } = from;

    if (
        typeof pathname !== "string" ||
        !pathname.startsWith("/") ||
        pathname.startsWith("//") ||
        pathname.includes("\\") ||
        AUTH_PAGES.includes(pathname)
    ) {
        return HOME;
    }

    return (
        pathname +
        (typeof search === "string" && search.startsWith("?") ? search : "") +
        (typeof hash === "string" && hash.startsWith("#") ? hash : "")
    );
}
