import { useState } from "react";

import { useUpdateCurrency } from "../../hooks/currencies/updatecurrency";

const NAME_MAX = 50;
const SYMBOL_MAX = 10;

/**
 * Rename a currency, change its symbol, or delete it. A rename carries the
 * offers and transactions along; the server refuses to delete a currency
 * they refer to, and says so: its message is shown as is.
 */
export function CurrencySettings({
    currencyId,
    name,
    symbol,
    onChanged,
    onDeleted,
}: {
    currencyId: number;
    name: string;
    symbol: string | null;
    onChanged: () => void;
    onDeleted: () => void;
}) {
    const { updateInfo, remove, loading, error } = useUpdateCurrency();
    const [newName, setNewName] = useState(name);
    const [newSymbol, setNewSymbol] = useState(symbol ?? "");

    const trimmedName = newName.trim();
    const trimmedSymbol = newSymbol.trim();
    const nameChanged = trimmedName !== name;
    const symbolChanged = trimmedSymbol !== (symbol ?? "");
    const valid =
        trimmedName.length > 0 &&
        trimmedName.length <= NAME_MAX &&
        trimmedSymbol.length > 0 &&
        trimmedSymbol.length <= SYMBOL_MAX;

    const submit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!valid || (!nameChanged && !symbolChanged)) return;

        const changes: { name?: string; symbol?: string } = {};
        if (nameChanged) changes.name = trimmedName;
        if (symbolChanged) changes.symbol = trimmedSymbol;
        if (await updateInfo(currencyId, changes)) onChanged();
    };

    const onDelete = async () => {
        if (!window.confirm(`Supprimer la monnaie « ${name} » ?`)) return;
        if (await remove(currencyId)) onDeleted();
    };

    return (
        <form className="info-row" onSubmit={submit}>
            <label>
                Nom{" "}
                <input
                    type="text"
                    maxLength={NAME_MAX}
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                />
            </label>
            <label>
                Symbole{" "}
                <input
                    type="text"
                    maxLength={SYMBOL_MAX}
                    value={newSymbol}
                    onChange={(e) => setNewSymbol(e.target.value)}
                />
            </label>
            <button
                type="submit"
                className="button"
                disabled={loading || !valid || (!nameChanged && !symbolChanged)}
            >
                Enregistrer
            </button>
            <button
                type="button"
                className="button"
                disabled={loading}
                onClick={onDelete}
            >
                Supprimer la monnaie
            </button>
            {error && <p role="alert">{error}</p>}
        </form>
    );
}
