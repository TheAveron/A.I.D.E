// Loader to extract the map name from URL parameters
export function loader({ params }) {
    const page: string = params.mapname;
    return { page };
}