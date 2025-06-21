import {
    type RouteConfig,
    route,
    index,
    prefix,
} from "@react-router/dev/routes";

export default [
    // * matches all URLs, the ? makes it optional so it will match / as well
    route("/A.I.D.E", "./app/App.tsx", [
        index("./app/pages/home.tsx"),
        route("login", "./app/pages/login.tsx"),
        route("contribuer", "./app/pages/contribution.tsx"),

        ...prefix("maps", [
            ...prefix("archives", [
                index("./app/pages/maps/archiveslist.tsx"),
                route(":page", "./app/pages/maps/mappage.tsx"),
            ]),
            route("actual", "./app/pages/maps/currentmap.tsx"),
        ]),
        route("profile", "./app/pages/profile.tsx"),
        route("factions", "./app/pages/factionlist.tsx"),
        route("*", "./app/pages/404.tsx"),
    ]),
] satisfies RouteConfig;
