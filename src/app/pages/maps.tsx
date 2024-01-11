import { Link, useLoaderData } from "react-router-dom";
import previousArrow from "../../assets/images/previous.svg";

export function loader({ params }) {
    const page: string = params.mapname;
    return { page };
}

type pageLoader = {
    page: string
}


function Map() {
    const { page } = useLoaderData() as pageLoader;

    const actual_url = window.location;

    console.log(actual_url.origin)
    

    const doc_head = document.head.innerHTML;
    document.head.innerHTML = doc_head + '<link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/gh/openlayers/openlayers.github.io@master/en/v6.9.0/css/ol.css" integrity="sha256-jckPZk66EJrEBQXnJ5QC2bD+GxWPDRVVoMGr5vrMZvM=" crossorigin="anonymous"></script>'

    + '<script src="https://cdn.jsdelivr.net/gh/openlayers/openlayers.github.io@master/en/v6.9.0/build/ol.js" integrity="sha256-77dogUPZ1WVoK9BDF0CxsKnAouX3YzK6n4tIcbDgtFI=" crossOrigin="anonymous"></script>'

    + `<script type="text/javascript" src="${actual_url.origin}/Maps/${page}/unmined.map.properties.js"}></script>`
    + `<script type="text/javascript" src="${actual_url.origin}/Maps/${page}/unmined.map.regions.js"}></script>`
    + `<script type="text/javascript" src="${actual_url.origin}/Maps/${page}/unmined.map.players.js"></script>`
    + `<script type="text/javascript" src="${actual_url.origin}/Maps/${page}/custom.markers.js"></script>`
    + `<script type="text/javascript" src="${actual_url.origin}/Maps/${page}/unmined.openlayers.js"></script>`    
    + `<script type="text/javascript" src="${actual_url.origin}/scripts/maprendering.js"></script>`

    return <>
        <button id="previous"><img src={previousArrow} width={"20px"}/><Link to="/maps">  Retour</Link></button>
        <div id="map"></div>
    </>
}

export default Map