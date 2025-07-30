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
        route("register", "./app/pages/register.tsx"),
        route("contribuer", "./app/pages/contribution.tsx"),

        ...prefix("archives", [
            index("./app/pages/archives/archives.tsx"),

            ...prefix("rule:rule", [
                index("./app/pages/archives/rules/ruleslist.tsx"),
                route(":type/:name", "./app/pages/archives/rules/rulepage.tsx"),
            ]),

            ...prefix("maps", [
                route(":page", "./app/pages/archives/maps/mappage.tsx"),
            ]),
        ]),
        route("actual", "./app/pages/archives/maps/currentmap.tsx"),
        route("profile", "./app/pages/profile.tsx"),
        route("factions", "./app/pages/factionlist.tsx"),
        route("*", "./app/pages/404.tsx"),
    ]),
] satisfies RouteConfig;
