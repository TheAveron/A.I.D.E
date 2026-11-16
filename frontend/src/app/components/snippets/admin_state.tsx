import { Link } from "react-router";

import { useApiGet } from "../../utils/useapiget";
import type { AdminFactionState, AdminUserState } from "../../types/admin";

function counts(by: Record<string, number>): string {
    return `${by.OPEN ?? 0} ouvertes, ${by.CLOSED ?? 0} complétées, ${by.CANCELLED ?? 0} annulées`;
}

/** What the server knows of an account: read-only, to debug a report. */
export function UserState({ userId }: { userId: number }) {
    const { data, loading, error } = useApiGet<AdminUserState>(
        `/admin/users/${userId}/state`,
        "Erreur lors du chargement de l'état du compte",
    );
    if (error) return <p role="alert">{error}</p>;
    if (loading || !data) return <p>Chargement...</p>;

    return (
        <ul>
            <li>
                <b>Compte</b> : {" "}
                <Link to={`/user/${data.user.user_id}`}>
                    {data.user.username}
                </Link>{" "}
                (n°{data.user.user_id}), créé le{" "}
                {new Date(data.user.created_at).toLocaleDateString("fr-FR")}
            </li>
            <li>
                <b>Offres</b> : {counts(data.offers_by_status)}
            </li>
            <li>
                <b>Transactions</b> : {data.purchases} achats, {data.sales}{" "}
                ventes
            </li>
            <li>
                <b>Notifications non lues</b> : {data.unread_notifications}
            </li>
            <li>
                <b>Demande d&apos;adhésion en attente</b> :{" "}
                {data.pending_join_request ?? "aucune"}
            </li>
            <li>
                <b>Trains en service</b> : {data.trains_owned}
            </li>
            <li>
                <b>Version de session</b> : {data.token_version}
            </li>
        </ul>
    );
}

/** What the server knows of a faction: read-only, to debug a report. */
export function FactionState({ factionId }: { factionId: number }) {
    const { data, loading, error } = useApiGet<AdminFactionState>(
        `/admin/factions/${factionId}/state`,
        "Erreur lors du chargement de l'état de la faction",
    );
    if (error) return <p role="alert">{error}</p>;
    if (loading || !data) return <p>Chargement...</p>;

    return (
        <ul>
            <li>
                <b>Chef</b> : {data.leader ?? "aucun"}
            </li>
            <li>
                <b>Description</b> : {data.description || "-"}
            </li>
            <li>
                <b>Rôles</b> :
                {data.roles.length === 0
                    ? "aucun"
                    : data.roles
                          .map((r) => `${r.name} (${r.member_count})`)
                          .join(", ")}
            </li>
            <li>
                <b>Monnaie</b> :
                {data.currency
                    ? `${data.currency.name}, ${data.currency.total_in_circulation} en circulation`
                    : "aucune"}
            </li>
            <li>
                <b>Offres</b> : {counts(data.offers_by_status)}
            </li>
            <li>
                <b>Demandes d&apos;adhésion en attente</b> :{" "}
                {data.pending_join_requests}
            </li>
            <li>
                <b>Trains en service</b> : {data.trains_owned}
            </li>
        </ul>
    );
}
