import { type MouseEvent } from "react";
import { type Components } from "react-markdown";
import { Link } from "react-router-dom";
import { type ComponentProps } from "react";

export const components: Components = {
    a: ({ href, children }: ComponentProps<"a">) => {
        if (!href) return <span>{children}</span>;

        href = decodeURIComponent(href);

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
                        const target = document.querySelector(href);
                        if (target)
                            target.scrollIntoView({ behavior: "smooth" });
                    }}
                    target="_self"
                >
                    {children}
                </a>
            );
        }

        if (href.startsWith("http")) {
            return (
                <a href={href} target="_blank" rel="noopener noreferrer">
                    {children}
                </a>
            );
        }

        return <a href={href}>{children}</a>;
    },
};
