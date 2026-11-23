import { Suspense, useEffect, useState, type MouseEvent } from "react";

import ReactMarkdown, {
    defaultUrlTransform,
    type Components,
} from "react-markdown";
import { GoBackButton } from "../components/common/return";
import remarkGfm from "remark-gfm";
import rehypeSlug from "rehype-slug";

import { Link as RouterLink, useLocation } from "react-router";
import {
    decodeMarkdownHref,
    getDocumentRoute,
    isSafeExternalHref,
    isSafeInternalHref,
    resolveRelativeDocumentLink,
} from "./safe_markdown_link";

type DocParams = {
    /** The API route of the document (it answers { title, content }). */
    url: string;
    /** The page route under which its "doc://" links are opened. */
    linkBase: string;
    /** Whether `content` lacks the "# title" heading, to put back. */
    withTitle?: boolean;
};

function slugPreserveAccents(value: string) {
    return value
        .toLowerCase()
        .replace(/[^\w\s\-àâäéèêëîïôöùûüç]/g, "") // allow accented chars
        .replace(/\s+/g, "-");
}

/**
 * react-markdown empties the URLs of unknown protocols, "doc://" included:
 * keep those, the `a` component below turns them into in-app routes.
 */
function keepDocLinks(url: string) {
    return url.startsWith("doc://") ? url : defaultUrlTransform(url);
}

function DocuLoader({ url, linkBase, withTitle = false }: DocParams) {
    const { pathname } = useLocation();
    const [content, setContent] = useState<string>("");
    const [error, setError] = useState<string>("");
    const [retryKey, setRetryKey] = useState(0);

    useEffect(() => {
        const controller = new AbortController();
        setContent("");
        setError("");
        fetch(url, { signal: controller.signal })
            .then(async (response) => {
                if (!response.ok) throw new Error("Failed to load markdown");
                const doc = await response.json();
                setContent(
                    withTitle
                        ? `# ${doc.title}\n\n${doc.content}`
                        : doc.content,
                );
            })
            .catch((err) => {
                if (err instanceof DOMException && err.name === "AbortError") {
                    return;
                }
                console.error(err);
                setError("Impossible de charger le document.");
            });

        return () => controller.abort();
    }, [url, withTitle, retryKey]);

    const components: Components = {
        a: ({ href, children }) => {
            if (!href) return <span>{children}</span>;

            href = decodeMarkdownHref(href) ?? "";
            if (!href) return <span>{children}</span>;

            if (href.startsWith("doc://")) {
                const docName = href.replace("doc://", "");
                return (
                    <RouterLink to={getDocumentRoute(docName, linkBase)}>
                        {children}
                    </RouterLink>
                );
            }

            if (href.startsWith("#")) {
                return (
                    <a
                        href={href}
                        onClick={(e: MouseEvent<HTMLAnchorElement>) => {
                            e.preventDefault();
                            const target = document.getElementById(
                                href.slice(1),
                            );
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

            // "../zones/spawn", "ursa": another document of the same section
            const relative = resolveRelativeDocumentLink(
                href,
                pathname,
                linkBase,
            );
            if (relative) {
                return <RouterLink to={relative}>{children}</RouterLink>;
            }

            return <span>{children}</span>;
        },
    };

    return (
        <Suspense fallback={<div>Page is Loading...</div>}>
            <GoBackButton />
            <section className="text-section" style={{ paddingBottom: "10vh" }}>
                {error ? (
                    <div>
                        <p>{error}</p>
                        <button
                            type="button"
                            className="button"
                            onClick={() => setRetryKey((value) => value + 1)}
                        >
                            Réessayer
                        </button>
                    </div>
                ) : (
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        rehypePlugins={[
                            [rehypeSlug, { slug: slugPreserveAccents }],
                        ]}
                        components={components}
                        urlTransform={keepDocLinks}
                    >
                        {content || "# Loading..."}
                    </ReactMarkdown>
                )}
            </section>
        </Suspense>
    );
}

export default DocuLoader;
