/* eslint-disable @typescript-eslint/no-var-requires */
/**
 * Map.tsx
 *
 * This component renders an iframe view of a specific map page in the Cube Crusader application.
 * It uses a loader to receive the `mapname` route param and conditionally shows the iframe after
 * a user interaction. Legacy DOM manipulation is removed in favor of React state and effects.
 */

import { useLoaderData, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import previousArrow from "../../assets/images/previous.svg";

// Loader to extract the map name from URL parameters
export function loader({ params }) {
    const page: string = params.mapname;
    return { page };
}

type PageLoader = {
    page: string;
};

function Map() {
    const { page } = useLoaderData() as PageLoader;
    const [showIframe, setShowIframe] = useState(false);

    // Optional: Hide footer and previous button when iframe is displayed
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
                <>
                    <button id="previous" className="nav-button">
                        <img src={previousArrow} width="20px" alt="Back" />
                        <Link to="/A.I.D.E/maps"> Retour</Link>
                    </button>

                    <button id="render" onClick={() => setShowIframe(true)}>
                        Render
                    </button>
                </>
            )}

            {showIframe && (
                <iframe
                    title={`Map Viewer for ${page}`}
                    style={{
                        width: "100vw",
                        height: "calc(100vh - max(8vh, calc(4vh + 50px)))",
                        border: "none",
                    }}
                    src={`/A.I.D.E/Maps/${page}/unmined.index.html`}
                />
            )}
        </>
    );
}

export default Map;
