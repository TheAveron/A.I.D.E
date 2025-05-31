import { useEffect, useState, Suspense } from "react";
import { useLoaderData } from "react-router-dom";
import md_converter from "../utils/markdown_converter";
import { GoBackButton } from "../components/goback_button";

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
    const { page } = useLoaderData() as pageLoader;
    const [content, setContent] = useState(<></>);

    useEffect(() => {
        fetch(`/A.I.D.E/Rules/${folder}/${page}.md`)
            .then(async (response) => {
                if (!response.ok) throw new Error('Failed to load markdown');
                const text = await response.text();
                setContent(md_converter(text) as JSX.Element);
            })
            .catch(error => {
                console.error(error);
                setContent(<p>Error loading content.</p>);
            });
    }, [folder, page]);

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
