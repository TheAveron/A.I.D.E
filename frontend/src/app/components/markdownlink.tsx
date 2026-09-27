import { type MouseEvent } from "react";
import { type Components } from "react-markdown";
import { Link } from "react-router";
import { type ComponentProps } from "react";
import {
    decodeMarkdownHref,
    isSafeExternalHref,
    isSafeInternalHref,
} from "../utils/safe_markdown_link";

export const components: Components = {
    a: ({ href, children }: ComponentProps<"a">) => {
        if (!href) return <span>{children}</span>;

        href = decodeMarkdownHref(href) ?? "";
        if (!href) return <span>{children}</span>;

        if (href.startsWith("doc://")) {
            const docName = href.replace("doc://", "");
            return <Link to={`/documents/${docName}`}>{children}</Link>;
        }

        if (href.startsWith("#")) {
            return (
                <a
                    href={href}
                    onClick={(e: MouseEvent<HTMLAnchorElement>) => {
                        e.preventDefault();
                        const target = document.getElementById(href.slice(1));
                        if (target)
                            target.scrollIntoView({ behavior: "smooth" });
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

        return <span>{children}</span>;
    },
};
