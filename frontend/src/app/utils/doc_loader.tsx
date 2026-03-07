import { Suspense, useEffect, useState, type MouseEvent } from "react";

import ReactMarkdown, { type Components } from "react-markdown";
import { GoBackButton } from "../components/buttons/return";
import remarkGfm from "remark-gfm";
import rehypeSlug from "rehype-slug";

import { Link as RouterLink } from "react-router-dom";

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

    useEffect(() => {
        setContent("");
        fetch(
            folder
                ? `/documents/${server}/faction_doc/${folder}/${page}`
                : `/documents/${server}/doc/${page}`,
        )
            .then(async (response) => {
                if (!response.ok) throw new Error("Failed to load markdown");
                const text = await response.json();
                setContent(text.content);
            })
            .catch((err) => {
                console.error(err);
                setError("Error loading content.");
            });
    }, [server, folder, page]);

    const components: Components = {
        a: ({ href, children }) => {
            if (!href) return <span>{children}</span>;

            href = decodeURIComponent(href);

            if (href.startsWith("doc://")) {
                const docName = href.replace("doc://", "");
                return (
                    <RouterLink to={`/documents/${docName}`}>
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

    return (
        <Suspense fallback={<div>Page is Loading...</div>}>
            <GoBackButton />
            <section className="text-section" style={{ paddingBottom: "10vh" }}>
                {error ? (
                    <p>{error}</p>
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
