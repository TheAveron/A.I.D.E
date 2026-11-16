import { Links, Meta, Outlet, Scripts, ScrollRestoration } from "react-router";
import logo from "./assets/images/CC_logo.png";
import { THEME_BOOT_SCRIPT } from "./app/utils/theme";

export function Layout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="fr" data-theme="dark" suppressHydrationWarning>
            <head>
                <meta charSet="UTF-8" />
                <script
                    dangerouslySetInnerHTML={{ __html: THEME_BOOT_SCRIPT }}
                />
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
