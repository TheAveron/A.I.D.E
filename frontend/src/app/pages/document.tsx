import axios from "axios";
import { components } from "../components/markdownlink";

import { useEffect, useState, Suspense } from "react";
import { useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSlug from "rehype-slug";

import { GoBackButton } from "../components/buttons/return";

interface PageType {
    title: string;
    content: string;
}

function slugPreserveAccents(value: string) {
    return value
        .toLowerCase()
        .replace(/[^\w\s\-àâäéèêëîïôöùûüç]/g, "") // allow accented chars
        .replace(/\s+/g, "-");
}

export default function DocumentPage() {
    const { server, faction, page } = useParams();
    const [content, setContent] = useState<string>("# Loading...");
    const [error, setError] = useState<string>("");

    useEffect(() => {
        if (!server) {
            setError("No server name provided");
            return;
        }

        if (!faction) {
            setError("No faction name provided");
            return;
        }

        if (!page) {
            setError("No document name provided");
            return;
        }

        setContent("# Loading...");
        axios
            .get<PageType>(
                `http://localhost:8000/documents/${server}/${faction}/${page}`
            )
            .then((res) => {
                try {
                    setContent(res.data.content);
                } catch {
                    setError("Document format error");
                }
            })
            .catch(() => {
                setError("Document not found");
            });
    }, [server, faction, page]);

    if (error) {
        return <div className="p-4 text-red-600 font-bold">{error}</div>;
    }

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
