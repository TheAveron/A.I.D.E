import { GoBackButton } from "../../../components/common/return";
import { useFullscreenMap } from "../../../hooks/network/fullscreen_map";
import MapViewer from "../../../components/network/map_viewer";
import { CURRENT_MAP_FOLDER, getLabelFromFolder } from "../../../utils/maps";

/** The current server's map: the native viewer, with the factions' overlays. */
function ActualMap() {
    useFullscreenMap();

    return (
        <>
            <div id="map-header" className="column-layout">
                <GoBackButton />
                <div id="map-title">
                    <h2>{getLabelFromFolder(CURRENT_MAP_FOLDER)}</h2>
                </div>
            </div>
            <MapViewer folder={CURRENT_MAP_FOLDER} />
        </>
    );
}

export default ActualMap;
