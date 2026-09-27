import { Suspense, useEffect, useState, type MouseEvent } from "react";

import ReactMarkdown, { type Components } from "react-markdown";
import { GoBackButton } from "../components/buttons/return";
import remarkGfm from "remark-gfm";
import rehypeSlug from "rehype-slug";

import { Link as RouterLink } from "react-router";
import {
    decodeMarkdownHref,
    getDocumentRoute,
    isSafeExternalHref,
    isSafeInternalHref,
} from "./safe_markdown_link";

type DocParams = {
    server: string;
    page: string;
    folder?: string;
};

function slugPreserveAccents(value: string) {
    return value
        .toLowerCase()
        .replace(/[^\w\s\-àâäéèêëîïôöùûüç]/g, "") // allow accented chars
        .replace(/\s+/g, "-");
}

function DocuLoader({ server, page, folder }: DocParams) {
    const [content, setContent] = useState<string>("");
    const [error, setError] = useState<string>("");
    const [retryKey, setRetryKey] = useState(0);

    useEffect(() => {
        const controller = new AbortController();
        setContent("");
        setError("");
        fetch(
            folder
                ? `/documents/${server}/faction_doc/${folder}/${page}`
                : `/documents/${server}/doc/${page}`,
            { signal: controller.signal },
        )
            .then(async (response) => {
                if (!response.ok) throw new Error("Failed to load markdown");
                const text = await response.json();
                setContent(text.content);
            })
            .catch((err) => {
                if (err instanceof DOMException && err.name === "AbortError") {
                    return;
                }
                console.error(err);
                setError("Error loading content.");
            });

        return () => controller.abort();
    }, [server, folder, page, retryKey]);

    const components: Components = {
        a: ({ href, children }) => {
            if (!href) return <span>{children}</span>;

            href = decodeMarkdownHref(href) ?? "";
            if (!href) return <span>{children}</span>;

            if (href.startsWith("doc://")) {
                const docName = href.replace("doc://", "");
                return (
                    <RouterLink to={getDocumentRoute(docName)}>
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
                    >
                        {content || "# Loading..."}
                    </ReactMarkdown>
                )}
            </section>
        </Suspense>
    );
}

export default DocuLoader;
