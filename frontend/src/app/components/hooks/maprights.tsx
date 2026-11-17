import type { MarkerType, TerritoryType } from "../../types/map";
import { useMe } from "./me";
import { useRole } from "./role";

/**
 * What the logged-in user may change on the map, by the same rules as the API:
 * a faction's territories and points need manage_territory in that faction,
 * a player's own points need nothing, and admins can change everything.
 */
export function useMapRights() {
    const { user, loading: userLoading } = useMe();
    const { role, loading: roleLoading } = useRole(user?.role_id ?? null);

    const isAdmin = !!user?.is_admin;
    // The faction the user can draw for, if any
    const factionId =
        role?.manage_territory && user?.faction_id ? user.faction_id : null;

    const canManageFaction = (id: number): boolean =>
        isAdmin || (factionId !== null && factionId === id);

    const canEditTerritory = (territory: TerritoryType): boolean =>
        canManageFaction(territory.faction_id);

    const canEditMarker = (marker: MarkerType): boolean => {
        if (!user) return false;
        if (marker.user_id !== null) {
            return isAdmin || marker.user_id === user.user_id;
        }
        return (
            marker.faction_id !== null && canManageFaction(marker.faction_id)
        );
    };

    return {
        user,
        loggedIn: !!user,
        isAdmin,
        factionId,
        canEditTerritory,
        canEditMarker,
        loading: userLoading || roleLoading,
    };
}
