/* eslint-disable @typescript-eslint/no-var-requires */
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

    function render2() {
        const render_block = document.getElementById("render")
        if (render_block) render_block.style.display = "none"

        const footer_block = document.getElementById("footer")
        if (footer_block) footer_block.style.display = "none"

        const previous_block = document.getElementById("previous")
        if (previous_block) {
            previous_block.style.display = "none"
        }


        const content = document.getElementById("content")
        if (content) content.innerHTML += `<iframe style="width:100vw; height:calc(100vh - max(8vh, calc(4vh + 50px)))" src="/A.I.D.E/Maps/${page}/unmined.index.html"></iframe>`
    }

    return <>
        <button id="previous"><img src={previousArrow} width={"20px"} /><Link to="/A.I.D.E/maps">  Retour</Link></button>
        <button id="render" onClick={render2}>Render</button>
    </>
}

export default Map