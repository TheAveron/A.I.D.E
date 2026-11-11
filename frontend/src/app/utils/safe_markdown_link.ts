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
