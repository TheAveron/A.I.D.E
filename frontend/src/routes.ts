import {
    type RouteConfig,
    route,
    index,
    prefix,
    layout,
} from "@react-router/dev/routes";

export default [
    // * matches all URLs, the ? makes it optional so it will match / as well
    route("/A.I.D.E", "./app/App.tsx", [
        index("./app/pages/home.tsx"),
        route("login", "./app/pages/login.tsx"),
        route("register", "./app/pages/register.tsx"),

        layout("./app/utils/requireauth.tsx", [
            route("contribuer", "./app/pages/contribution.tsx"),
            route("factions", "./app/pages/factions.tsx"),
            route("profile", "./app/pages/profile.tsx"),
            route("offers", "./app/pages/offers.tsx"),
            route("faction/:factionid", "./app/pages/faction_page.tsx"),
            route("user/:userid", "./app/pages/user_page.tsx"),
        ]),

        ...prefix("archives", [
            index("./app/pages/archives/archives.tsx"),

            ...prefix("rules", [
                index("./app/pages/archives/rules/ruleslist.tsx"),
                route("/:server/:faction/:page", "./app/pages/document.tsx"),
            ]),

            ...prefix("maps", [
                route(":page", "./app/pages/archives/maps/mappage.tsx"),
            ]),
        ]),
        route("actual", "./app/pages/archives/maps/currentmap.tsx"),
        route("*", "./app/pages/404.tsx"),
    ]),
] satisfies RouteConfig;
