/**
 * Map.tsx
 *
 * An archived map: renders the iframe of the map given by the `page` route param.
 * The header is folded away while it is displayed (see hooks/fullscreen_map.ts).
 */

import { useParams } from "react-router";
import ServerPage from "../server";

function Map() {
    const { page } = useParams();

    return ServerPage(page ?? "");
}

export default Map;
