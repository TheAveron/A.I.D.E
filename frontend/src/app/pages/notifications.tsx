import { Link } from "react-router";

import {
    useNotificationActions,
    useNotifications,
} from "../components/hooks/notifications";

/** The logged-in user's notifications, newest first. */
export default function NotificationsPage() {
    const { notifications, loading, error } = useNotifications();
    const {
        markRead,
        markAllRead,
        error: actionError,
    } = useNotificationActions();
    const unread = notifications.filter((n) => !n.is_read).length;

    return (
        <div className="information-container">
            <div className="snippet-container">
                <h2>Notifications</h2>
                {unread > 0 && (
                    <button
                        type="button"
                        className="button"
                        onClick={markAllRead}
                    >
                        Tout marquer comme lu
                    </button>
                )}
                {(error || actionError) && (
                    <p role="alert">{error ?? actionError}</p>
                )}
                {loading ? (
                    <p>Chargement...</p>
                ) : notifications.length === 0 ? (
                    <p className="empty-state">Aucune notification.</p>
                ) : (
                    <ul>
                        {notifications.map((n) => (
                            <li
                                key={n.notification_id}
                                style={{
                                    fontWeight: n.is_read ? "normal" : "bold",
                                }}
                            >
                                <small>
                                    {new Date(n.created_at).toLocaleString()}
                                </small>{" "}
                                {n.link ? (
                                    <Link
                                        to={n.link}
                                        onClick={() =>
                                            !n.is_read &&
                                            markRead(n.notification_id)
                                        }
                                    >
                                        {n.message}
                                    </Link>
                                ) : (
                                    n.message
                                )}{" "}
                                {!n.is_read && (
                                    <button
                                        type="button"
                                        className="button"
                                        onClick={() =>
                                            markRead(n.notification_id)
                                        }
                                    >
                                        Lu
                                    </button>
                                )}
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
}
