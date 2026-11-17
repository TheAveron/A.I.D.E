import {
    type RouteConfig,
    route,
    index,
    prefix,
    layout,
} from "@react-router/dev/routes";

const aideRoutes = [
    index("./app/pages/home.tsx"),

    route("login", "./app/pages/auth/login.tsx"),
    route("register", "./app/pages/auth/register.tsx"),

    layout("./app/utils/requireauth.tsx", [
        route("contribuer", "./app/pages/contribution.tsx"),
        route("factions", "./app/pages/factions/factions.tsx"),
        route("profile", "./app/pages/users/profile.tsx"),
        route("offers", "./app/pages/offers/offers.tsx"),
        route("transactions", "./app/pages/offers/transactions.tsx"),
        route("notifications", "./app/pages/users/notifications.tsx"),
        route("trains", "./app/pages/network/trains.tsx"),
        route("trains/new", "./app/pages/network/train_new.tsx"),
        route("train/:trainid", "./app/pages/network/train_page.tsx"),
        route("lines", "./app/pages/network/lines.tsx"),
        route("line/:code", "./app/pages/network/line_page.tsx"),
        route("stations", "./app/pages/network/stations.tsx"),
        route("station/:stationid", "./app/pages/network/station_page.tsx"),
        route("admin", "./app/pages/admin/admin.tsx"),

        route("faction/:factionid", "./app/pages/factions/faction_page.tsx"),
        route(
            "faction/:factionid/documents/new",
            "./app/pages/factions/document_editor.tsx",
            { id: "document-new" },
        ),
        route(
            "faction/:factionid/documents/:docname/edit",
            "./app/pages/factions/document_editor.tsx",
            { id: "document-edit" },
        ),
        route("user/:userid", "./app/pages/users/user_page.tsx"),
    ]),

    ...prefix("archives", [
        index("./app/pages/archives/archives.tsx"),

        ...prefix("documentation", [
            route("CubeCrusaders", "./app/pages/archives/docs/cc_docslist.tsx"),
            route("AgeOfSteam", "./app/pages/archives/docs/aos_doclist.tsx"),
            route("/:server/:page", "./app/pages/archives/docs/document.tsx"),
            route(
                "/:server/:folder/:page",
                "./app/pages/archives/docs/faction_document.tsx",
            ),
        ]),

        ...prefix("maps", [
            route(":page", "./app/pages/archives/maps/mappage.tsx"),
        ]),
    ]),

    route("actual", "./app/pages/archives/maps/currentmap.tsx"),
    route("network", "./app/pages/network/network.tsx"),

    route(
        "documentation/AgeOfSteam",
        "./app/pages/archives/docs/currentdoc.tsx",
    ),

    route("*", "./app/pages/404.tsx"),
];

export default [route("/", "./app/App.tsx", aideRoutes)] satisfies RouteConfig;
