import { Link } from "react-router";
import CurrencyCell from "../snippets/currency_cell";
import MemberCounter from "../snippets/member_count";
import type { FactionType } from "../../types/factions";
import { useMe } from "../hooks/me";
import { useRole } from "../hooks/role";
import { UpdateFactionButton } from "../buttons/joinfaction";

type Props = {
    factions: FactionType[];
    loading: boolean;
    error: string | null;
    page: number;
    totalPages: number;
    setPage: (val: number) => void;
    onRetry: () => void;
};

export default function FactionTable({
    factions,
    loading,
    error,
    page,
    totalPages,
    setPage,
    onRetry,
}: Props) {
    const next = () => setPage(Math.min(page + 1, totalPages));
    const prev = () => setPage(Math.max(page - 1, 1));

    const { user } = useMe();
    const { role } = useRole(user?.role_id ?? null);

    return (
        <div className="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Nom</th>
                        <th>Description</th>
                        <th>Nombre de membres</th>
                        <th>Monnaie</th>
                        <th>Satut</th>
                        {role?.name != "Chef" ? <th>Action</th> : <></>}
                    </tr>
                </thead>
                <tbody>
                    {!error ? (
                        !loading ? (
                            factions.length > 0 ? (
                                factions.map((faction) => (
                                    <>
                                        <Link
                                            key={faction.faction_id}
                                            to={
                                                faction.name != "Sans Faction"
                                                    ? `/A.I.D.E/faction/${faction.faction_id}`
                                                    : ""
                                            }
                                            style={{ display: "table-row" }}
                                        >
                                            <td>{faction.name}</td>

                                            <td className="faction-description">
                                                {faction.description?.trim() ||
                                                    "Pas de description"}
                                            </td>
                                            <td>
                                                <MemberCounter
                                                    faction_id={faction.faction_id.toString()}
                                                />
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

                                            {role?.name != "Chef" && user ? (
                                                role?.faction_id !=
                                                faction.faction_id ? (
                                                    <td>
                                                        <div
                                                            onClick={(event) => {
                                                                event.preventDefault();
                                                                event.stopPropagation();
                                                            }}
                                                        >
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
                                                            />
                                                        </div>
                                                    </td>
                                                ) : (
                                                    <td></td>
                                                )
                                            ) : (
                                                <></>
                                            )}
                                        </Link>
                                    </>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan={5} className="empty-state">
                                        Aucune faction trouvée.
                                    </td>
                                </tr>
                            )
                        ) : (
                            <tr>
                                <td colSpan={5}>Chargement des factions...</td>
                            </tr>
                        )
                    ) : (
                        <tr>
                            <td colSpan={5} style={{ color: "red" }}>
                                {error}
                                <button type="button" onClick={onRetry}>
                                    Réessayer
                                </button>
                            </td>
                        </tr>
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
