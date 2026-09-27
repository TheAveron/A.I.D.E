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
