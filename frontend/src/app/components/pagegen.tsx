import { MAP_LABELS } from "../utils/maps";
import { useFullscreenMap } from "./hooks/fullscreen_map";

/** The iframe of an archived map, shown as soon as the page opens. */
function PageGenerator(page: string) {
    // Only the maps listed in utils/maps.ts can be embedded
    const safePage = Object.prototype.hasOwnProperty.call(MAP_LABELS, page)
        ? page
        : null;

    useFullscreenMap(safePage !== null);

    if (!safePage) {
        return <p role="alert">Cette carte n'existe pas.</p>;
    }

    return (
        <iframe
            title={`Map Viewer for ${safePage}`}
            src={`/maps/${safePage}/index.html`}
            sandbox="allow-scripts"
            style={{ width: "100%", height: "96vh", border: "none" }}
        />
    );
}

export default PageGenerator;
