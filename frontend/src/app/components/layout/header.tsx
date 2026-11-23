import {
    useEffect,
    useId,
    useRef,
    useState,
    type MouseEvent as ReactMouseEvent,
    type ReactNode,
} from "react";
import { Link, useLocation } from "react-router";

import { useAuth } from "../../utils/authcontext";
import { useMe } from "../../hooks/users/me";
import { useUnreadCount } from "../../hooks/users/notifications";
import {
    NAV_SECTIONS,
    findActive,
    visibleItems,
    type NavSection,
} from "../../utils/navigation";

/** Runs `close` when a click lands on a link: the menus close after navigating. */
const closeOnLink = (close: () => void) => (event: ReactMouseEvent) => {
    if ((event.target as HTMLElement).closest("a")) close();
};

/**
 * The navigation: on a wide screen it is part of the header, on a narrow one
 * it hides behind a menu button (with a dot when there are unread notifications).
 */
function NavShell({
    unread = 0,
    children,
}: {
    unread?: number;
    children: ReactNode;
}) {
    const [open, setOpen] = useState(false);
    const navId = useId();

    useEffect(() => {
        if (!open) return;
        const onKey = (event: KeyboardEvent) => {
            if (event.key === "Escape") setOpen(false);
        };
        document.addEventListener("keydown", onKey);
        return () => document.removeEventListener("keydown", onKey);
    }, [open]);

    return (
        <>
            <button
                type="button"
                className="nav-toggle"
                aria-expanded={open}
                aria-controls={navId}
                aria-label={
                    unread > 0
                        ? `Menu (${unread} notifications non lues)`
                        : "Menu"
                }
                onClick={() => setOpen((current) => !current)}
            >
                <span className="nav-toggle-bars" aria-hidden="true" />
                {unread > 0 && <span className="nav-dot" aria-hidden="true" />}
            </button>
            <nav
                id={navId}
                className={open ? "open" : undefined}
                aria-label="Navigation principale"
                onClick={closeOnLink(() => setOpen(false))}
            >
                {children}
            </nav>
        </>
    );
}

/**
 * A menu of the header: a button that opens a list of links. On a narrow
 * screen the button gives way to a plain title and the links are listed
 * under it.
 */
function NavDropdown({
    label,
    active = false,
    align = "start",
    children,
}: {
    label: ReactNode;
    active?: boolean;
    align?: "start" | "end";
    children: ReactNode;
}) {
    const [open, setOpen] = useState(false);
    const wrapperRef = useRef<HTMLDivElement>(null);
    const buttonRef = useRef<HTMLButtonElement>(null);
    const menuId = useId();
    const { pathname } = useLocation();

    // Another page: the menu closes (also when it was reached another way)
    useEffect(() => setOpen(false), [pathname]);

    useEffect(() => {
        if (!open) return;
        const onPointerDown = (event: MouseEvent) => {
            if (!wrapperRef.current?.contains(event.target as Node)) {
                setOpen(false);
            }
        };
        const onKey = (event: KeyboardEvent) => {
            if (event.key === "Escape") {
                setOpen(false);
                buttonRef.current?.focus();
            }
        };
        document.addEventListener("mousedown", onPointerDown);
        document.addEventListener("keydown", onKey);
        return () => {
            document.removeEventListener("mousedown", onPointerDown);
            document.removeEventListener("keydown", onKey);
        };
    }, [open]);

    const classes = ["nav-more"];
    if (open) classes.push("open");
    if (align === "end") classes.push("nav-more-end");

    return (
        <div
            ref={wrapperRef}
            className={classes.join(" ")}
            onClick={closeOnLink(() => setOpen(false))}
        >
            <button
                ref={buttonRef}
                type="button"
                className={active ? "link nav-more-toggle active" : "link nav-more-toggle"}
                aria-expanded={open}
                aria-controls={menuId}
                onClick={() => setOpen((current) => !current)}
            >
                {label}
            </button>
            <span className="nav-group-title" aria-hidden="true">
                {label}
            </span>
            <div id={menuId} className="nav-menu">
                {children}
            </div>
        </div>
    );
}

/** A section of the site: a menu of its pages, or a link if it has one. */
function SectionMenu({
    section,
    loggedIn,
}: {
    section: NavSection;
    loggedIn: boolean;
}) {
    const { pathname } = useLocation();
    const { section: activeSection, item: activeItem } = findActive(pathname);
    const items = visibleItems(section, loggedIn);
    const active = activeSection?.id === section.id;

    if (items.length === 0) return null;
    if (items.length === 1) {
        return (
            <Link
                className={active ? "link active" : "link"}
                to={items[0].to}
                aria-current={active ? "page" : undefined}
            >
                {section.label}
            </Link>
        );
    }
    return (
        <NavDropdown label={section.label} active={active}>
            {items.map((item) => (
                <Link
                    key={item.to}
                    className="link"
                    to={item.to}
                    aria-current={item === activeItem ? "page" : undefined}
                >
                    {item.label}
                </Link>
            ))}
        </NavDropdown>
    );
}

/** The map: a page of its own, not part of a section. */
function MapLink() {
    const { pathname } = useLocation();
    const active = pathname === "/actual";
    return (
        <Link
            className={active ? "link active" : "link"}
            to="/actual"
            aria-current={active ? "page" : undefined}
        >
            Carte
        </Link>
    );
}

/** The notifications link: a bell with the number of unread ones. */
function NotificationsLink({ count }: { count: number }) {
    return (
        <Link
            className="link nav-notifications"
            to="/notifications"
            aria-label={
                count > 0
                    ? `Notifications (${count} non lues)`
                    : "Notifications"
            }
        >
            <svg
                className="nav-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
            >
                <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
                <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
            </svg>
            <span className="nav-label">Notifications</span>
            {count > 0 && (
                <span className="nav-badge" aria-hidden="true">
                    {count > 99 ? "99+" : count}
                </span>
            )}
        </Link>
    );
}

/** The account menu: profile, administration (staff only), logout. */
function AccountMenu() {
    const { user } = useMe();
    const { logout } = useAuth();
    const { pathname } = useLocation();
    const active = ["/profile", "/admin"].includes(pathname);

    return (
        <NavDropdown
            align="end"
            active={active}
            label={
                <>
                    <svg
                        className="nav-icon"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        aria-hidden="true"
                    >
                        <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
                        <circle cx="12" cy="7" r="4" />
                    </svg>
                    <span>{user?.username ?? "Compte"}</span>
                </>
            }
        >
            <Link
                className="link"
                to="/profile"
                aria-current={pathname === "/profile" ? "page" : undefined}
            >
                Mon profil
            </Link>
            {!!user?.global_roles?.length && (
                <Link
                    className="link"
                    to="/admin"
                    aria-current={pathname === "/admin" ? "page" : undefined}
                >
                    Administration
                </Link>
            )}
            <button type="button" className="link nav-logout" onClick={logout}>
                Déconnexion
            </button>
        </NavDropdown>
    );
}

function LoggedInNav() {
    const { count } = useUnreadCount();

    return (
        <NavShell unread={count}>
            <div className="nav-links">
                <MapLink />
                {NAV_SECTIONS.map((section) => (
                    <SectionMenu key={section.id} section={section} loggedIn />
                ))}
            </div>
            <div className="nav-account">
                <NotificationsLink count={count} />
                <AccountMenu />
            </div>
        </NavShell>
    );
}

function LoggedOutNav() {
    return (
        <NavShell>
            <div className="nav-links">
                <MapLink />
                {NAV_SECTIONS.map((section) => (
                    <SectionMenu
                        key={section.id}
                        section={section}
                        loggedIn={false}
                    />
                ))}
            </div>
            <div className="nav-account">
                <Link className="button" id="signin" to="/login">
                    Connexion
                </Link>
            </div>
        </NavShell>
    );
}

function Header() {
    const { token } = useAuth();

    return (
        <header id="header">
            <Link to="" className="title link">
                Cube Crusader
            </Link>
            {token ? <LoggedInNav /> : <LoggedOutNav />}
        </header>
    );
}

export default Header;
