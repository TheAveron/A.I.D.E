/**
 * Map.tsx
 *
 * An archived map: renders the iframe of the map given by the `page` route param.
 * The header is folded away while it is displayed (see hooks/fullscreen_map.ts).
 */

import { useParams } from "react-router";
import ServerPage from "../server";
import NotFound from "../../404";
import { LISTED_MAPS } from "../../../utils/maps";

function Map() {
    const { page } = useParams();

    // Only the former servers' maps: the current one is at /actual
    if (!page || !LISTED_MAPS.includes(page)) return <NotFound />;
    return ServerPage(page);
}

export default Map;
