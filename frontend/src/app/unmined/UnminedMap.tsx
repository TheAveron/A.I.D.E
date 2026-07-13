import React, { useEffect, useRef } from "react";

// Imports from your converted TSX modules
import { Unmined } from "./unmined";
import { UnminedMapProperties } from "../unmined.map.properties";
import { UnminedRegions } from "../unmined.map.regions";
import { UnminedPlayers } from "../unmined.map.players";
import { UnminedCustomMarkers } from "../custom.markers";

// CSS imports (assuming you moved them to npm or local styles)
import "ol/ol.css";
import "ol-contextmenu/dist/ol-contextmenu.css";
import "toastify-js/src/toastify.css";
import "../index.css";

const UnminedMap: React.FC = () => {
    const mapRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        // Set page title
        document.title = `${UnminedMapProperties.worldName} - uNmINeD`;

        // Merge custom markers
        if (
            UnminedCustomMarkers?.isEnabled &&
            UnminedCustomMarkers.markers?.length > 0
        ) {
            UnminedMapProperties.markers = [
                ...UnminedMapProperties.markers,
                ...UnminedCustomMarkers.markers,
            ];
        }

        // Create player markers
        if (UnminedPlayers?.length > 0) {
            UnminedMapProperties.playerMarkers =
                Unmined.createPlayerMarkers(UnminedPlayers);
        }

        // Initialize map
        if (mapRef.current) {
            new Unmined(mapRef.current, UnminedMapProperties, UnminedRegions);
        }
    }, []);

    return (
        <div id="map" ref={mapRef} style={{ width: "100%", height: "100vh" }} />
    );
};

export default UnminedMap;
