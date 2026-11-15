import { Link } from "react-router";

import { useAuth } from "../utils/authcontext";
import { useUnreadCount } from "./hooks/notifications";

/** The notifications link, with the number of unread ones; only for a logged-in user. */
function NotificationsLink() {
    const { count } = useUnreadCount();
    return (
        <Link
            className="link"
            to="/notifications"
            aria-label={
                count > 0
                    ? `Notifications (${count} non lues)`
                    : "Notifications"
            }
        >
            Notifications{count > 0 && ` (${count > 99 ? "99+" : count})`}
        </Link>
    );
}

function Header() {
    const { token } = useAuth() ?? {};

    return (
        <header id="header">
            <Link to="" className="title link">
                Cube Crusader
            </Link>
            <nav>
                <Link className="link" to="/actual">
                    Carte
                </Link>
                <Link className="link" to="/documentation/AgeOfSteam">
                    Documentation
                </Link>

                {token ? (
                    <>
                        <Link className="link" to="/factions">
                            Factions
                        </Link>
                        <Link className="link" to="/offers">
                            Offres
                        </Link>
                        <Link className="link" to="/transactions">
                            Transactions
                        </Link>
                        <Link className="link" to="/contribuer">
                            Contribuer
                        </Link>
                        <NotificationsLink />
                        <Link className="link" to="/profile">
                            Profil
                        </Link>
                    </>
                ) : (
                    <>
                        <Link className="link" to="/archives">
                            Archives
                        </Link>
                        <Link className="button" id="signin" to="/login">
                            Connexion
                        </Link>
                    </>
                )}
            </nav>
        </header>
    );
}

export default Header;
