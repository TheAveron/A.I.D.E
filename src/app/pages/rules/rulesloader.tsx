export function loader({ params }) {
    const page: string = params.rulename;
    const server: string = params.server;
    return { page, server };
}
