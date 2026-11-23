import type { ReactNode } from "react";
import { useLocation } from "react-router";

import SectionIcon from "./section_icon";
import { findActive } from "../../utils/navigation";

/**
 * The top of a page: the icon and color of its section, the section's name
 * above the title, one sentence on what the page is for, and its actions
 * (create, open...) on the right.
 */
export default function PageHeader({
    title,
    description,
    actions,
    section,
}: {
    title: ReactNode;
    description?: ReactNode;
    actions?: ReactNode;
    /** Forced section ("admin"...); by default the one of the address. */
    section?: { id: string; label: string };
}) {
    const { pathname } = useLocation();
    const current = section ?? findActive(pathname).section;
    const id = current?.id ?? "ressources";

    return (
        <div className={`page-header page-header-${id}`}>
            <SectionIcon section={id} className="page-header-icon" />
            <div className="page-header-text">
                {current && <p className="page-header-eyebrow">{current.label}</p>}
                <h1>{title}</h1>
                {description && <p className="page-header-description">{description}</p>}
            </div>
            {actions && <div className="page-header-actions">{actions}</div>}
        </div>
    );
}
