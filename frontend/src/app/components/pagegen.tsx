import { useState, useEffect } from "react";
import { GoBackButton } from "./return";

function PageGenerator(page: string, render: boolean) {
    const [showIframe, setShowIframe] = useState(render);

    useEffect(() => {
        if (!showIframe) return;

        const renderBlock = document.getElementById("render");
        const footerBlock = document.getElementById("footer");
        const previousBlock = document.getElementById("previous");

        if (renderBlock) renderBlock.style.display = "none";
        if (footerBlock) footerBlock.style.display = "none";
        if (previousBlock) previousBlock.style.display = "none";

        return () => {
            if (renderBlock) renderBlock.style.display = "";
            if (footerBlock) footerBlock.style.display = "";
            if (previousBlock) previousBlock.style.display = "";
        };
    }, [showIframe]);

    return (
        <>
            {!showIframe && (
                <section style={{ rowGap: "5vh" }}>
                    <GoBackButton />
                    <button
                        className="button"
                        id="render"
                        onClick={() => setShowIframe(true)}
                    >
                        <p>Render</p>
                    </button>
                </section>
            )}

            {showIframe && (
                <iframe
                    title={`Map Viewer for ${page}`}
                    src={`/A.I.D.E/Maps/${page}/unmined.index.html`}
                    style={{ width: "100%", height: "100vh", border: "none" }}
                />
            )}
        </>
    );
}

export default PageGenerator;
