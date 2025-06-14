import {
    Links,
    Meta,
    Outlet,
    Scripts,
    ScrollRestoration,
} from "react-router";

export function Layout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="fr" data-theme="light" >
            <head>
                <meta charSet="UTF-8" />
                <link rel="icon" type="image/png" href="/images/CC_logo.png" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <link rel="stylesheet" type="text/css"
                    href="https://cdn.jsdelivr.net/gh/openlayers/openlayers.github.io@master/en/v6.9.0/css/ol.css"
                    integrity="sha256-jckPZk66EJrEBQXnJ5QC2bD+GxWPDRVVoMGr5vrMZvM=" crossOrigin="anonymous" />

                <script src="https://cdn.jsdelivr.net/gh/openlayers/openlayers.github.io@master/en/v6.9.0/build/ol.js"
                    integrity="sha256-77dogUPZ1WVoK9BDF0CxsKnAouX3YzK6n4tIcbDgtFI=" crossOrigin="anonymous"></script>
                <title>Guide de CubeCrusader</title>
                <Meta />
                <Links />
            </head>
            <body>
                {children}
                <ScrollRestoration />
                <Scripts />
            </body>
        </html >
    );
}

export default function Root() {
    return <Outlet />;
}
