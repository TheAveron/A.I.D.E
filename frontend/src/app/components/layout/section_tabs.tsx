import { Link, useLocation } from "react-router";

import { useAuth } from "../../utils/authcontext";
import { findActive, visibleItems } from "../../utils/navigation";

/**
 * The pages of the section being visited, as tabs at the top of the content
 * (Lignes, Gares, Trains...), the current one marked. Nothing outside of a
 * section, nor for a section with a single page.
 */
export default function SectionTabs() {
    const { pathname } = useLocation();
    const { token } = useAuth();
    const { section, item } = findActive(pathname);
    if (!section) return null;

    const items = visibleItems(section, !!token);
    if (items.length < 2) return null;

    return (
        <nav className="section-tabs" aria-label={section.label}>
            <span className="section-tabs-title">{section.label}</span>
            <ul>
                {items.map((entry) => (
                    <li key={entry.to}>
                        <Link
                            to={entry.to}
                            aria-current={entry === item ? "page" : undefined}
                        >
                            {entry.label}
                        </Link>
                    </li>
                ))}
            </ul>
        </nav>
    );
}
