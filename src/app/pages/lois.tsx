import md_converter from "../utils/markdown_converter"
import { useEffect, useState } from "react"
import { Link, useLoaderData } from "react-router-dom";
import "../../assets/styles/goback.css"
import previousArrow from "../../assets/images/previous.svg"

export function loader({ params }) {
    const page: string = params.rulename;
    return { page };
}

type LoiParams = {
    folder: string
}

type pageLoader = {
    page: string
}

function Loi({ folder }: LoiParams) {
    const { page }: pageLoader = useLoaderData();
    const [content, setContent] = useState(<></>);
    useEffect(() => {
        fetch(`/Rules/${folder}/${page}.md`)
            .then(async (response) => setContent(md_converter(await response.text())))
            .catch(error => console.log(error))
    });

    return <>
        <button id="previous"><img src={previousArrow} width={"20px"}/><Link to="../../Rules">  Retour</Link></button>
        <section className="text-section">{content}</section>
    </>
}

export default Loi