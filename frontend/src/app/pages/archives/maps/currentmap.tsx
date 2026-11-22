import { useState } from "react";

import { GoBackButton } from "../../../components/common/return";
import { useFullscreenMap } from "../../../hooks/network/fullscreen_map";
import MapViewer from "../../../components/network/map_viewer";
import {
    CURRENT_MAP_FOLDER,
    CURRENT_MAP_VARIANTS,
    getLabelFromFolder,
} from "../../../utils/maps";

/** The current server's map: the native viewer, with the factions' overlays. */
function ActualMap() {
    useFullscreenMap();
    const [folder, setFolder] = useState(CURRENT_MAP_FOLDER);

    return (
        <>
            <div id="map-header" className="column-layout">
                <GoBackButton />
                <div id="map-title">
                    <h2>{getLabelFromFolder(CURRENT_MAP_FOLDER)}</h2>
                </div>
            </div>
            {/* The switch floats over the map, outside the viewer: it stays
                there while a dimension loads, or if its export is missing */}
            <div className="map-stage">
                {/* One viewer per export: the view starts again on the new map */}
                <MapViewer key={folder} folder={folder} />
                {CURRENT_MAP_VARIANTS.length > 1 && (
                    <div
                        className="map-dimensions map-float"
                        role="tablist"
                        aria-label="Dimension"
                    >
                        {CURRENT_MAP_VARIANTS.map((variant) => (
                            <button
                                key={variant.folder}
                                type="button"
                                role="tab"
                                aria-selected={variant.folder === folder}
                                className={
                                    variant.folder === folder
                                        ? "map-dimension active"
                                        : "map-dimension"
                                }
                                onClick={() => setFolder(variant.folder)}
                            >
                                {variant.label}
                            </button>
                        ))}
                    </div>
                )}
            </div>
        </>
    );
}

export default ActualMap;
