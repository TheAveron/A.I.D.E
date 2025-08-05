import { useState, useEffect } from "react";

import "../../assets/css/components/section.css";
import "../../assets/css/components/buttons.css";

function toggleLayout(isColumn: boolean) {
    const mapTitle = document.getElementById("map-title");
    if (isColumn) {
        mapTitle?.classList.add("column-layout");
    } else {
        mapTitle?.classList.remove("column-layout");
    }
}

function PageGenerator(page: string, render: boolean) {
    const [showIframe, setShowIframe] = useState(render);
    let isColumn = true;

    useEffect(() => {
        if (!showIframe) return;

        const renderBlock = document.getElementById("render");
        const footerBlock = document.getElementById("footer");
        const headerBlock = document.getElementById("header");
        const previousBlock = document.getElementById("previous");

        const main = document.getElementById("main");
        isColumn = !isColumn;
        toggleLayout(isColumn);

        if (renderBlock) renderBlock.style.display = "none";
        if (footerBlock) footerBlock.style.display = "none";
        if (headerBlock) {
            headerBlock.style.height = "0vh";
            headerBlock.style.minHeight = "0";
            headerBlock.style.paddingTop = "0";
            headerBlock.style.paddingBottom = "0";
            headerBlock.style.borderBottomWidth = "0";
        }

        if (previousBlock) previousBlock.style.top = "2vh";

        if (main) main.style.marginTop = "0";

        return () => {
            if (renderBlock) renderBlock.style.display = "";
            if (footerBlock) footerBlock.style.display = "";
            if (headerBlock) {
                headerBlock.style.display = "4vh";
                headerBlock.style.minHeight = "75px";
                headerBlock.style.paddingTop = " 2vh";
                headerBlock.style.paddingBottom = " 2vh";
                headerBlock.style.borderBottomWidth = "1px";
            }

            if (previousBlock) previousBlock.style.top = "var(--header-height)";
            if (main) main.style.marginTop = "var(--header-height)";

            isColumn = !isColumn;
            toggleLayout(isColumn);
        };
    }, [showIframe]);

    return (
        <>
            {!showIframe && (
                <section style={{ rowGap: "5vh" }}>
                    <button
                        className="button"
                        id="render"
                        onClick={() => setShowIframe(true)}
                    >
                        <p>Afficher</p>
                    </button>
                </section>
            )}

            {showIframe && (
                <iframe
                    title={`Map Viewer for ${page}`}
                    src={`/A.I.D.E/Maps/${page}/unmined.index.html`}
                    style={{ width: "100%", height: "96vh", border: "none" }}
                />
            )}
        </>
    );
}

export default PageGenerator;
