import { Link } from "react-router";
import CurrencyCell from "../snippets/currency_cell";
import type { FactionType } from "../../types/factions";
import { useMe } from "../hooks/me";
import { useRole } from "../hooks/role";
import { UpdateFactionButton } from "../buttons/joinfaction";

const NO_FACTION = "Sans Faction";

type Props = {
    factions: FactionType[];
    memberCounts: Record<string, number>;
    // Called once the user has joined a faction
    onJoined: () => void;
    loading: boolean;
    error: string | null;
    page: number;
    totalPages: number;
    setPage: (val: number) => void;
    onRetry: () => void;
};

export default function FactionTable({
    factions,
    memberCounts,
    onJoined,
    loading,
    error,
    page,
    totalPages,
    setPage,
    onRetry,
}: Props) {
    const next = () => setPage(Math.min(page + 1, totalPages));
    const prev = () => setPage(Math.max(page - 1, 1));

    const { user, refresh: refreshMe } = useMe();
    const { role } = useRole(user?.role_id ?? null);

    const showActions = role?.name != "Chef";
    const columns = showActions ? 6 : 5;

    return (
        <div className="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Nom</th>
                        <th>Description</th>
                        <th>Nombre de membres</th>
                        <th>Monnaie</th>
                        <th>Statut</th>
                        {showActions && <th>Action</th>}
                    </tr>
                </thead>
                <tbody>
                    {error ? (
                        <tr>
                            <td colSpan={columns} style={{ color: "red" }}>
                                {error}
                                <button type="button" onClick={onRetry}>
                                    Réessayer
                                </button>
                            </td>
                        </tr>
                    ) : loading ? (
                        <tr>
                            <td colSpan={columns}>
                                Chargement des factions...
                            </td>
                        </tr>
                    ) : factions.length === 0 ? (
                        <tr>
                            <td colSpan={columns} className="empty-state">
                                Aucune faction trouvée.
                            </td>
                        </tr>
                    ) : (
                        factions.map((faction) => {
                            const isNoFaction = faction.name === NO_FACTION;
                            return (
                                <tr key={faction.faction_id}>
                                    <td>
                                        {isNoFaction ? (
                                            faction.name
                                        ) : (
                                            <Link
                                                to={`/faction/${faction.faction_id}`}
                                            >
                                                {faction.name}
                                            </Link>
                                        )}
                                    </td>
                                    <td className="faction-description">
                                        {faction.description?.trim() ||
                                            "Pas de description"}
                                    </td>
                                    <td>
                                        {memberCounts[faction.faction_id] ?? 0}
                                    </td>
                                    <td>
                                        <CurrencyCell
                                            factionId={faction.faction_id.toString()}
                                        />
                                    </td>
                                    <td>
                                        <div
                                            className={`status ${
                                                faction.is_approved
                                                    ? "approved"
                                                    : "not-approved"
                                            }`}
                                        >
                                            {faction.is_approved
                                                ? "Validée \u2705"
                                                : "En attente \u23f3"}
                                        </div>
                                    </td>
                                    {showActions && (
                                        <td>
                                            {user &&
                                                !isNoFaction &&
                                                user.faction_id !=
                                                    faction.faction_id && (
                                                    <UpdateFactionButton
                                                        userId={user.user_id}
                                                        currentFactionId={
                                                            user.faction_id
                                                        }
                                                        currentRoleId={
                                                            user.role_id
                                                        }
                                                        factionId={
                                                            faction.faction_id
                                                        }
                                                        onUpdate={() => {
                                                            refreshMe();
                                                            onJoined();
                                                        }}
                                                    />
                                                )}
                                        </td>
                                    )}
                                </tr>
                            );
                        })
                    )}
                </tbody>
            </table>
            {totalPages > 1 && (
                <div className="pagination">
                    <button onClick={prev} disabled={page === 1}>
                        ◀ Précédent
                    </button>
                    <span>
                        Page {page} / {totalPages}
                    </span>
                    <button onClick={next} disabled={page === totalPages}>
                        Suivant ▶
                    </button>
                </div>
            )}
        </div>
    );
}
