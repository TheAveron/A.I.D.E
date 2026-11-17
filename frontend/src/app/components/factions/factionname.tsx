import { useFaction } from "../../hooks/factions/faction";

export default function Factionname({ factionId }: { factionId: string }) {
    const { faction } = useFaction(factionId);

    return <span className="username">{faction?.name}</span>;
}
