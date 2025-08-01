import { Links, Meta, Outlet, Scripts, ScrollRestoration } from "react-router";
import logo from "./assets/images/CC_logo.png";

export function Layout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="fr" data-theme="dark">
            <head>
                <meta charSet="UTF-8" />
                <link rel="icon" type="image/png" href={logo} />
                <meta
                    name="viewport"
                    content="width=device-width, initial-scale=1.0"
                />
                <title>Guide de CubeCrusader</title>
                <Meta />
                <Links />
            </head>
            <body>
                {children}
                <ScrollRestoration />
                <Scripts />
            </body>
        </html>
    );
}

export default function Root() {
    return <Outlet />;
}
