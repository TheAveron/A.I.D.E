import axios from "axios";
import { components } from "../components/markdownlink";

import { useEffect, useState, Suspense } from "react";
import { useParams } from "react-router";
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
    const [retryKey, setRetryKey] = useState(0);

    useEffect(() => {
        const controller = new AbortController();
        setError("");

        if (!server) {
            setError("No server name provided");
            return () => controller.abort();
        }

        if (!faction) {
            setError("No faction name provided");
            return () => controller.abort();
        }

        if (!page) {
            setError("No document name provided");
            return () => controller.abort();
        }

        setContent("# Loading...");
        axios
            .get<PageType>(`/documents/${server}/${faction}/${page}`, {
                signal: controller.signal,
            })
            .then((res) => {
                try {
                    setContent(res.data.content);
                } catch {
                    setError("Document format error");
                }
            })
            .catch((requestError) => {
                if (axios.isCancel(requestError)) return;
                setError("Document not found");
            });
        return () => controller.abort();
    }, [server, faction, page, retryKey]);

    if (error) {
        return (
            <div className="p-4 text-red-600 font-bold">
                <p>{error}</p>
                <button
                    type="button"
                    className="button"
                    onClick={() => setRetryKey((value) => value + 1)}
                >
                    Réessayer
                </button>
            </div>
        );
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
