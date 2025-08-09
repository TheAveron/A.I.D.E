import { useCurrency } from "../hooks/factioncurrency";

export default function CurrencyCell({ factionId }: { factionId: string }) {
    const { currency, loading, error } = useCurrency(factionId);

    if (error) return <p className="error-text">{error}</p>;
    if (loading) return <p>Chargement...</p>;
    return <>{currency?.name || "Pas de monnaie"}</>;
}
