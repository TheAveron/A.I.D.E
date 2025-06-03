import { useEffect, useState, Suspense } from "react";
import { useLoaderData } from "react-router-dom";
import md_converter from "../../utils/markdown_converter";
import { GoBackButton } from "../../components/goback_button";


type LoiParams = {
    type: string
}

type pageLoader = {
    page: string
    server: string
}

function Loi({ type }: LoiParams) {
    const { page, server } = useLoaderData() as pageLoader;
    const [content, setContent] = useState(<></>);

    console.log(`Loading content for ${server}/${type}/${page}`);

    useEffect(() => {
        fetch(`/A.I.D.E/Rules/${server}/${type}/${page}.md`)
            .then(async (response) => {
                if (!response.ok) throw new Error('Failed to load markdown');
                const text = await response.text();
                setContent(md_converter(text) as JSX.Element);
            })
            .catch(error => {
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
