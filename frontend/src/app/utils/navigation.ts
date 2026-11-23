/**
 * The map of the site: every section and its pages, in one place. The header
 * builds its menus from it, and the tabs under the header show the pages of
 * the section being visited.
 */

export interface NavItem {
    to: string;
    label: string;
    /**
     * Paths that belong to this page, besides `to` itself: "/line/" makes
     * "/line/A" part of "Lignes". A prefix ending in "/" matches below it,
     * any other one matches itself or below it.
     */
    match?: string[];
    /** Reachable without an account. */
    public?: boolean;
}

export interface NavSection {
    id: string;
    label: string;
    items: NavItem[];
}

export const NAV_SECTIONS: NavSection[] = [
    {
        id: "economie",
        label: "Économie",
        items: [
            { to: "/factions", label: "Factions", match: ["/faction/"] },
            { to: "/offers", label: "Marché" },
            { to: "/transactions", label: "Transactions" },
        ],
    },
    {
        id: "reseau",
        label: "Réseau ferré",
        items: [
            { to: "/network", label: "Plan du réseau", public: true },
            { to: "/lines", label: "Lignes", match: ["/line/"] },
            { to: "/stations", label: "Gares", match: ["/station/"] },
            { to: "/trains", label: "Trains", match: ["/train/"] },
        ],
    },
    {
        id: "ressources",
        label: "Ressources",
        items: [
            { to: "/documentation", label: "Documentation", public: true },
            {
                to: "/documentation/AgeOfSteam/normes_ferroviaires",
                label: "Normes ferroviaires",
                public: true,
            },
            {
                to: "/schematiques",
                label: "Schematics",
                match: ["/schematique/"],
            },
            { to: "/archives", label: "Archives", public: true },
            { to: "/contribuer", label: "Contribuer" },
        ],
    },
];

/** How well `pathname` matches `pattern` (its length), or -1. */
function matchLength(pathname: string, pattern: string): number {
    if (pattern.endsWith("/")) {
        return pathname.startsWith(pattern) ? pattern.length : -1;
    }
    return pathname === pattern || pathname.startsWith(`${pattern}/`)
        ? pattern.length
        : -1;
}

/**
 * The section and page `pathname` belongs to. The longest match wins, so
 * the standards page is "Normes ferroviaires", not "Documentation".
 */
export function findActive(pathname: string): {
    section: NavSection | null;
    item: NavItem | null;
} {
    let best = { section: null as NavSection | null, item: null as NavItem | null };
    let bestLength = -1;
    for (const section of NAV_SECTIONS) {
        for (const item of section.items) {
            for (const pattern of [item.to, ...(item.match ?? [])]) {
                const length = matchLength(pathname, pattern);
                if (length > bestLength) {
                    bestLength = length;
                    best = { section, item };
                }
            }
        }
    }
    return best;
}

/** The items of a section that the visitor may open. */
export function visibleItems(section: NavSection, loggedIn: boolean): NavItem[] {
    return loggedIn ? section.items : section.items.filter((i) => i.public);
}
