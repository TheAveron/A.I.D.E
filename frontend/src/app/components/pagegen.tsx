import { useState, useEffect } from "react";

const allowedMapPages = new Set([
    "OCube_crusader",
    "OLSLN",
    "OLSPLW_zoom",
    "OStrong_world_zoom",
    "OSurvival_islands_zoom",
    "OUtopia_zoom",
    "EUtopia_zoom",
]);

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
    const safePage = allowedMapPages.has(page) ? page : null;
    useEffect(() => {
        if (!showIframe) return;

        const renderBlock = document.getElementById("render");
        const footerBlock = document.getElementById("footer");
        const headerBlock = document.getElementById("header");
        const previousBlock = document.getElementById("previous");

        const main = document.getElementById("main");
        toggleLayout(false);

        if (renderBlock) renderBlock.style.display = "none";
        if (footerBlock) footerBlock.style.display = "none";
        if (headerBlock) {
            headerBlock.style.height = "0vh";
            headerBlock.style.minHeight = "0";
            headerBlock.style.paddingTop = "0";
            headerBlock.style.paddingBottom = "0";
            headerBlock.style.borderBottomWidth = "0";
        }

        if (previousBlock) previousBlock.style.top = "unset";

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

            toggleLayout(true);
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

            {showIframe && safePage && (
                <iframe
                    title={`Map Viewer for ${safePage}`}
                    src={`/A.I.D.E/maps/${safePage}/index.html`}
                    sandbox="allow-scripts"
                    style={{ width: "100%", height: "96vh", border: "none" }}
                />
            )}
        </>
    );
}

export default PageGenerator;
