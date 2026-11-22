import { useState } from "react";

import { useUpdateCurrency } from "../../hooks/currencies/updatecurrency";

const MAX_TOTAL = 2147483647; // same bound as the server

export function UpdateCurrencyTotal({
    currencyId,
    currentTotal,
    onUpdated,
}: {
    currencyId: number;
    currentTotal: number;
    onUpdated: () => void;
}) {
    const { updateTotal, loading, error } = useUpdateCurrency();
    const [total, setTotal] = useState(String(currentTotal));
    const [notes, setNotes] = useState("");

    const value = total.trim() === "" ? NaN : Number(total);
    const valid = Number.isInteger(value) && value >= 0 && value <= MAX_TOTAL;
    const unchanged = value === currentTotal;

    const submit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!valid || unchanged) return;

        if (await updateTotal(currencyId, value, notes)) {
            setNotes("");
            onUpdated();
        }
    };

    return (
        <form className="info-row" onSubmit={submit}>
            <label>
                Nouvelle quantité en circulation{" "}
                <input
                    type="number"
                    min="0"
                    max={MAX_TOTAL}
                    step="1"
                    value={total}
                    onChange={(e) => setTotal(e.target.value)}
                />
            </label>
            <label>
                Motif (facultatif){" "}
                <input
                    type="text"
                    maxLength={500}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                />
            </label>
            <button
                type="submit"
                className="button"
                disabled={loading || !valid || unchanged}
            >
                {loading ? "Mise à jour..." : "Mettre à jour"}
            </button>
            {error && <p role="alert">{error}</p>}
        </form>
    );
}
