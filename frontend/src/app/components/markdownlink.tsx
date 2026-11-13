import { type ComponentProps, type MouseEvent } from "react";
import { type Components } from "react-markdown";
import { Link, useLocation } from "react-router";
import {
    decodeMarkdownHref,
    getDocumentRoute,
    isSafeExternalHref,
    isSafeInternalHref,
    resolveRelativeDocumentLink,
} from "../utils/safe_markdown_link";

// eslint-disable-next-line react-refresh/only-export-components
function MarkdownLink({ href, children }: ComponentProps<"a">) {
    const { pathname } = useLocation();

    if (!href) return <span>{children}</span>;

    href = decodeMarkdownHref(href) ?? "";
    if (!href) return <span>{children}</span>;

    if (href.startsWith("doc://")) {
        const docName = href.replace("doc://", "");
        return <Link to={getDocumentRoute(docName)}>{children}</Link>;
    }

    if (href.startsWith("#")) {
        return (
            <a
                href={href}
                onClick={(e: MouseEvent<HTMLAnchorElement>) => {
                    e.preventDefault();
                    const target = document.getElementById(href.slice(1));
                    if (target) target.scrollIntoView({ behavior: "smooth" });
                }}
                target="_self"
            >
                {children}
            </a>
        );
    }

    if (isSafeExternalHref(href)) {
        return (
            <a href={href} target="_blank" rel="noopener noreferrer">
                {children}
            </a>
        );
    }

    if (isSafeInternalHref(href)) {
        return <a href={href}>{children}</a>;
    }

    // "../zones/spawn" or "citadelle_paix": another document, relative to this one
    const documentRoute = resolveRelativeDocumentLink(href, pathname);
    if (documentRoute) {
        return <Link to={documentRoute}>{children}</Link>;
    }

    return <span>{children}</span>;
}

export const components: Components = {
    a: MarkdownLink,
};
