import axios from "axios";
import { useState, type FormEvent } from "react";
import { Link } from "react-router";

import { useAdminCurrencies } from "../../hooks/admin/admin";
import { useFactions } from "../../hooks/factions/factions";
import { getErrorMessage } from "../../utils/apierror";
import type { AdminCurrencyType } from "../../types/admin";

const INT32_MAX = 2147483647;

function CurrencyEditor({
    currency,
    onDone,
}: {
    currency: AdminCurrencyType;
    onDone: (message: string, changed: boolean) => void;
}) {
    const [open, setOpen] = useState(false);
    const [name, setName] = useState(currency.name);
    const [symbol, setSymbol] = useState(currency.symbol ?? "");
    const [total, setTotal] = useState(String(currency.total_in_circulation));
    const [notes, setNotes] = useState("");
    const [busy, setBusy] = useState(false);

    const totalValue = Number(total);
    const valid =
        name.trim().length > 0 &&
        total.trim() !== "" &&
        Number.isInteger(totalValue) &&
        totalValue >= 0 &&
        totalValue <= INT32_MAX;

    const save = async (event: FormEvent) => {
        event.preventDefault();
        if (!valid) return;
        const changes: Record<string, string | number | null> = {};
        if (name.trim() !== currency.name) changes.name = name.trim();
        if (symbol.trim() !== (currency.symbol ?? "")) {
            changes.symbol = symbol.trim() || null;
        }
        if (totalValue !== currency.total_in_circulation) {
            changes.total_in_circulation = totalValue;
            if (notes.trim()) changes.notes = notes.trim();
        }
        if (Object.keys(changes).length === 0) {
            setOpen(false);
            return;
        }
        setBusy(true);
        try {
            await axios.put(
                `/admin/currencies/${currency.currency_id}`,
                changes,
            );
            onDone(`✅ Monnaie « ${currency.name} » modifiée`, true);
            setOpen(false);
        } catch (err) {
            onDone(`❌ ${getErrorMessage(err)}`, false);
        } finally {
            setBusy(false);
        }
    };

    const remove = async () => {
        if (
            !window.confirm(
                `Supprimer la monnaie « ${currency.name} » ? Impossible si des offres ou transactions l'utilisent.`,
            )
        ) {
            return;
        }
        setBusy(true);
        try {
            await axios.delete(`/admin/currencies/${currency.currency_id}`);
            onDone(`✅ Monnaie « ${currency.name} » supprimée`, true);
        } catch (err) {
            onDone(`❌ ${getErrorMessage(err)}`, false);
        } finally {
            setBusy(false);
        }
    };

    if (!open) {
        return (
            <>
                <button
                    type="button"
                    className="button"
                    onClick={() => setOpen(true)}
                >
                    Modifier
                </button>{" "}
                <button
                    type="button"
                    className="button"
                    disabled={busy}
                    onClick={remove}
                >
                    Supprimer
                </button>
            </>
        );
    }
    return (
        <form onSubmit={save}>
            <label>
                Nom
                <input
                    type="text"
                    maxLength={50}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                />
            </label>
            <label>
                Symbole
                <input
                    type="text"
                    maxLength={10}
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value)}
                />
            </label>
            <label>
                Total en circulation
                <input
                    type="number"
                    min="0"
                    step="1"
                    value={total}
                    onChange={(e) => setTotal(e.target.value)}
                />
            </label>
            <label>
                Motif du changement de total
                <input
                    type="text"
                    maxLength={500}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                />
            </label>
            <button type="submit" className="button" disabled={busy || !valid}>
                Enregistrer
            </button>
            <button
                type="button"
                className="button"
                onClick={() => setOpen(false)}
            >
                Fermer
            </button>
        </form>
    );
}

/**
 * Every currency: create, rename, correct the declared total, delete (for
 * admins and money admins). Who uses or issues a currency is managed from
 * the faction pages.
 */
export default function AdminCurrencies() {
    const { currencies, loading, error, refresh } = useAdminCurrencies();
    const { factions } = useFactions();
    const [message, setMessage] = useState("");

    const [name, setName] = useState("");
    const [symbol, setSymbol] = useState("");
    const [factionId, setFactionId] = useState("");
    const [busy, setBusy] = useState(false);

    // A faction uses one currency at most
    const taken = new Set(
        currencies.flatMap((c) => c.factions.map((f) => f.faction_id)),
    );
    const free = (factions ?? []).filter((f) => !taken.has(f.faction_id));

    const create = async (event: FormEvent) => {
        event.preventDefault();
        if (!name.trim() || !factionId) return;
        setBusy(true);
        setMessage("");
        try {
            await axios.post("/admin/currencies", {
                name: name.trim(),
                symbol: symbol.trim() || null,
                faction_id: Number(factionId),
            });
            setMessage(`✅ Monnaie « ${name.trim()} » créée`);
            setName("");
            setSymbol("");
            setFactionId("");
            refresh();
        } catch (err) {
            setMessage(`❌ ${getErrorMessage(err)}`);
        } finally {
            setBusy(false);
        }
    };

    return (
        <div className="snippet-container">
            <h2>Monnaies</h2>
            <form className="toolbar" onSubmit={create}>
                <input
                    type="text"
                    placeholder="Nom de la monnaie"
                    aria-label="Nom de la nouvelle monnaie"
                    maxLength={50}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                />
                <input
                    type="text"
                    placeholder="Symbole"
                    aria-label="Symbole de la nouvelle monnaie"
                    maxLength={10}
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value)}
                />
                <select
                    aria-label="Faction de la nouvelle monnaie"
                    value={factionId}
                    onChange={(e) => setFactionId(e.target.value)}
                >
                    <option value="">Faction sans monnaie...</option>
                    {free.map((f) => (
                        <option key={f.faction_id} value={f.faction_id}>
                            {f.name}
                        </option>
                    ))}
                </select>
                <button
                    type="submit"
                    className="button"
                    disabled={busy || !name.trim() || !factionId}
                >
                    Créer
                </button>
            </form>
            {message && <p role="status">{message}</p>}
            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Monnaie</th>
                            <th>Factions</th>
                            <th>Total en circulation</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {error ? (
                            <tr>
                                <td colSpan={4}>{error}</td>
                            </tr>
                        ) : loading ? (
                            <tr>
                                <td colSpan={4}>Chargement...</td>
                            </tr>
                        ) : currencies.length === 0 ? (
                            <tr className="empty-state">
                                <td colSpan={4}>Aucune monnaie.</td>
                            </tr>
                        ) : (
                            currencies.map((c) => (
                                <tr key={c.currency_id}>
                                    <td>
                                        {c.name}
                                        {c.symbol && (
                                            <small> ({c.symbol})</small>
                                        )}
                                    </td>
                                    <td>
                                        {c.factions.length === 0
                                            ? "-"
                                            : c.factions.map((f, i) => (
                                                  <span key={f.faction_id}>
                                                      {i > 0 && ", "}
                                                      <Link
                                                          to={`/faction/${f.faction_id}`}
                                                      >
                                                          {f.faction_name ??
                                                              `#${f.faction_id}`}
                                                      </Link>
                                                      {f.is_issuer && (
                                                          <small>
                                                              {" "}
                                                              (émettrice)
                                                          </small>
                                                      )}
                                                  </span>
                                              ))}
                                    </td>
                                    <td>{c.total_in_circulation}</td>
                                    <td>
                                        <CurrencyEditor
                                            key={`${c.name}/${c.symbol}/${c.total_in_circulation}`}
                                            currency={c}
                                            onDone={(text, changed) => {
                                                setMessage(text);
                                                if (changed) refresh();
                                            }}
                                        />
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
