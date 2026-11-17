import { useMe } from "../users/me";
import { useRole } from "../factions/role";

import type { TrainType } from "../../types/trains";

/** What the logged-in user may do with trains, lines and stations. */
export function useTrainRights() {
    const { user, loading: userLoading } = useMe();
    const { role, loading: roleLoading } = useRole(user?.role_id ?? null);

    const isTrainAdmin = !!user?.global_roles?.includes("train_admin");
    // manage_trains in the user's own faction
    const factionId =
        role?.manage_trains && user?.faction_id ? user.faction_id : null;

    const canManage = (train: TrainType): boolean =>
        isTrainAdmin ||
        (!!user && train.owner_user_id === user.user_id) ||
        (factionId !== null && train.owner_faction_id === factionId);

    return {
        user,
        isTrainAdmin,
        // The faction whose trains and lines the user can manage, if any
        factionId,
        canManage,
        loading: userLoading || roleLoading,
    };
}
