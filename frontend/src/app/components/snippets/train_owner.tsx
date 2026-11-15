import { Link } from "react-router";

import type { TrainType } from "../../types/trains";

/** The owner of a train, as a link to the player's or faction's page. */
export default function TrainOwner({ train }: { train: TrainType }) {
    if (train.owner_faction_id) {
        return (
            <Link to={`/faction/${train.owner_faction_id}`}>
                {train.owner_name ?? "Faction"}
            </Link>
        );
    }
    if (train.owner_user_id) {
        return (
            <Link to={`/user/${train.owner_user_id}`}>
                {train.owner_name ?? "Joueur"}
            </Link>
        );
    }
    return <>-</>;
}
