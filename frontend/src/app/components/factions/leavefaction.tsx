import { useFaction } from "../../hooks/factions/faction";
import { useMe } from "../../hooks/users/me";
import { useMemberCounts } from "../../hooks/factions/member_counts";
import { useMembership } from "../../hooks/factions/membership";
import { useRole } from "../../hooks/factions/role";
import { isLeaderRole } from "../../utils/roles";

const NO_FACTION = "Sans Faction";

/** Leave one's faction (not for its leader, nor without a faction). */
export function LeaveFactionButton() {
    const { user, refresh: refreshMe } = useMe();
    const { role } = useRole(user?.role_id ?? null);
    const { faction } = useFaction(user?.faction_id?.toString() ?? null);
    const { refresh: refreshCounts } = useMemberCounts();
    const { leave, loading, error } = useMembership();

    if (!user?.faction_id || faction?.name === NO_FACTION) return null;
    if (isLeaderRole(role)) return null;

    const onClick = async () => {
        if (!window.confirm("Quitter votre faction ?")) return;
        if (await leave()) {
            refreshMe();
            refreshCounts();
        }
    };

    return (
        <div className="snippet-container">
            <button
                type="button"
                className="button"
                disabled={loading}
                onClick={onClick}
            >
                Quitter ma faction
            </button>
            {error && <p role="alert">{error}</p>}
        </div>
    );
}
