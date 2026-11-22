import {
    useEffect,
    useId,
    useRef,
    useState,
    type MouseEvent as ReactMouseEvent,
    type ReactNode,
} from "react";
import { Link } from "react-router";

import { useAuth } from "../../utils/authcontext";
import { useMe } from "../../hooks/users/me";
import { useUnreadCount } from "../../hooks/users/notifications";

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

/** The rarely used pages, behind a "Plus" button (listed flat in the mobile menu). */
function MoreMenu({ children }: { children: ReactNode }) {
    const [open, setOpen] = useState(false);
    const wrapperRef = useRef<HTMLDivElement>(null);
    const buttonRef = useRef<HTMLButtonElement>(null);
    const menuId = useId();

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

    return (
        <div
            ref={wrapperRef}
            className={open ? "nav-more open" : "nav-more"}
            onClick={closeOnLink(() => setOpen(false))}
        >
            <button
                ref={buttonRef}
                type="button"
                className="link nav-more-toggle"
                aria-expanded={open}
                aria-controls={menuId}
                onClick={() => setOpen((current) => !current)}
            >
                Plus
            </button>
            <div id={menuId} className="nav-menu">
                {children}
            </div>
        </div>
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

/** The panel link, only for the server staff (admins and train admins). */
function AdminLink() {
    const { user } = useMe();
    if (!user?.global_roles?.length) return null;
    return (
        <Link className="link" to="/admin">
            Administration
        </Link>
    );
}

function LoggedInNav() {
    const { count } = useUnreadCount();
    const { logout } = useAuth();

    return (
        <NavShell unread={count}>
            <div className="nav-links">
                <Link className="link" to="/actual">
                    Carte
                </Link>
                <Link className="link" to="/factions">
                    Factions
                </Link>
                <Link className="link" to="/offers">
                    Offres
                </Link>
                <Link className="link" to="/trains">
                    Trains
                </Link>
                <MoreMenu>
                    <Link className="link" to="/network">
                        Réseau ferré
                    </Link>
                    <Link className="link" to="/documentation/AgeOfSteam">
                        Documentation
                    </Link>
                    <Link className="link" to="/archives">
                        Archives
                    </Link>
                    <Link className="link" to="/transactions">
                        Transactions
                    </Link>
                    <Link className="link" to="/contribuer">
                        Contribuer
                    </Link>
                    <AdminLink />
                </MoreMenu>
            </div>
            <div className="nav-account">
                <NotificationsLink count={count} />
                <Link className="link nav-profile" to="/profile">
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
                    <span>Profil</span>
                </Link>
                <button
                    type="button"
                    className="link nav-logout"
                    onClick={logout}
                >
                    Déconnexion
                </button>
            </div>
        </NavShell>
    );
}

function LoggedOutNav() {
    return (
        <NavShell>
            <div className="nav-links">
                <Link className="link" to="/actual">
                    Carte
                </Link>
                <Link className="link" to="/network">
                    Réseau ferré
                </Link>
                <Link className="link" to="/documentation/AgeOfSteam">
                    Documentation
                </Link>
                <Link className="link" to="/archives">
                    Archives
                </Link>
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
