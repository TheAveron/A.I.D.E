export function decodeMarkdownHref(href: string): string | null {
    try {
        return decodeURIComponent(href);
    } catch {
        return null;
    }
}

export function isSafeExternalHref(href: string): boolean {
    return /^https?:\/\//i.test(href);
}

export function isSafeInternalHref(href: string): boolean {
    return href.startsWith("/") && !href.startsWith("//");
}

export function getDocumentRoute(documentName: string): string {
    const segments = documentName
        .split("/")
        .filter((segment) => segment && segment !== "." && segment !== "..");

    return `/archives/documentation/${segments
        .map((segment) => encodeURIComponent(segment))
        .join("/")}`;
}

const DOCUMENTATION_PREFIX = "/archives/documentation/";

/**
 * The in-app route a relative link of a document points to, or null.
 *
 * Documents link to each other with relative paths ("../zones/spawn",
 * "citadelle_paix", optionally ending in ".md"), resolved like in a browser
 * against the address of the document being read. Only links that stay inside
 * the documentation are followed.
 */
export function resolveRelativeDocumentLink(
    href: string,
    currentPath: string,
): string | null {
    // Anything with a scheme ("mailto:", "javascript:"...) or starting with
    // "/", "//" or "#" is not a relative path.
    if (!href || /^[a-z][a-z0-9+.-]*:/i.test(href) || /^[/#\\]/.test(href)) {
        return null;
    }

    let resolved: URL;
    try {
        resolved = new URL(href, `http://local${currentPath}`);
    } catch {
        return null;
    }

    if (
        resolved.origin !== "http://local" ||
        !resolved.pathname.startsWith(DOCUMENTATION_PREFIX)
    ) {
        return null;
    }

    const pathname = resolved.pathname.replace(/\.md$/i, "");
    return pathname + resolved.hash;
}
