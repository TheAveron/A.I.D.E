import { useMembers } from "../hooks/factionmembers";

function MemberCounter({ faction_id }: { faction_id: string }) {
    const { users } = useMembers(faction_id);

    return <span className="amount">{users?.length}</span>;
}

export default MemberCounter;
