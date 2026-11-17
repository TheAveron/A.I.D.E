import { useFaction } from "../hooks/faction";
import { useMe } from "../hooks/me";
import { useMemberCounts } from "../hooks/member_counts";
import { useMembership } from "../hooks/membership";
import { useRole } from "../hooks/role";

const NO_FACTION = "Sans Faction";

/** Leave one's faction (not for its leader, nor without a faction). */
export function LeaveFactionButton() {
    const { user, refresh: refreshMe } = useMe();
    const { role } = useRole(user?.role_id ?? null);
    const { faction } = useFaction(user?.faction_id?.toString() ?? null);
    const { refresh: refreshCounts } = useMemberCounts();
    const { leave, loading, error } = useMembership();

    if (!user?.faction_id || faction?.name === NO_FACTION) return null;
    if (role?.name === "Chef") return null;

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
