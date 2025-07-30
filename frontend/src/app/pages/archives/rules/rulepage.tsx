import { useEffect, useState, Suspense, type JSX } from "react";
import { useParams } from "react-router-dom";
import md_converter from "../../../utils/mdconversion";
import { GoBackButton } from "../../../components/return";

type pageLoader = {
    page: string;
    server: string;
    type: string;
};

function Loi() {
    const { server, type, page } = useParams() as pageLoader;
    const [content, setContent] = useState(<></>);

    console.log(`Loading content for ${server}/${type}/${page}`);

    useEffect(() => {
        fetch(`/A.I.D.E/Rules/${server}/${type}/${page}.md`)
            .then(async (response) => {
                if (!response.ok) throw new Error("Failed to load markdown");
                const text = await response.text();
                setContent(md_converter(text) as JSX.Element);
            })
            .catch((error) => {
                console.error(error);
                setContent(<p>Error loading content.</p>);
            });
    }, [server, type, page]);

    return (
        <>
            <Suspense fallback={<div>Page is Loading...</div>}>
                <section className="text-section">
                    <GoBackButton />
                    {content}
                </section>
            </Suspense>
        </>
    );
}

export default Loi;
