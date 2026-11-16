import {
    type RouteConfig,
    route,
    index,
    prefix,
    layout,
} from "@react-router/dev/routes";

const aideRoutes = [
    index("./app/pages/home.tsx"),

    route("login", "./app/pages/login.tsx"),
    route("register", "./app/pages/register.tsx"),

    layout("./app/utils/requireauth.tsx", [
        route("contribuer", "./app/pages/contribution.tsx"),
        route("factions", "./app/pages/factions.tsx"),
        route("profile", "./app/pages/profile.tsx"),
        route("offers", "./app/pages/offers.tsx"),
        route("transactions", "./app/pages/transactions.tsx"),
        route("notifications", "./app/pages/notifications.tsx"),
        route("trains", "./app/pages/trains.tsx"),
        route("trains/new", "./app/pages/train_new.tsx"),
        route("train/:trainid", "./app/pages/train_page.tsx"),
        route("lines", "./app/pages/lines.tsx"),
        route("line/:code", "./app/pages/line_page.tsx"),
        route("stations", "./app/pages/stations.tsx"),
        route("station/:stationid", "./app/pages/station_page.tsx"),
        route("admin", "./app/pages/admin.tsx"),

        route("faction/:factionid", "./app/pages/faction_page.tsx"),
        route(
            "faction/:factionid/documents/new",
            "./app/pages/document_editor.tsx",
            { id: "document-new" },
        ),
        route(
            "faction/:factionid/documents/:docname/edit",
            "./app/pages/document_editor.tsx",
            { id: "document-edit" },
        ),
        route("user/:userid", "./app/pages/user_page.tsx"),
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

    route(
        "documentation/AgeOfSteam",
        "./app/pages/archives/docs/currentdoc.tsx",
    ),

    route("*", "./app/pages/404.tsx"),
];

export default [route("/", "./app/App.tsx", aideRoutes)] satisfies RouteConfig;
