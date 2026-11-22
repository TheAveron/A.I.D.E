import { useState } from "react";

import {
    useCurrencies,
    useCurrencyLinkActions,
    useFactionLinkRequests,
} from "../../hooks/currencies/currency_links";

/**
 * For a faction's holders of manage_funds: the currencies proposed to the
 * faction (accept or refuse), its own pending requests (withdraw), and, when
 * it uses no currency yet, a request to use an existing one.
 */
export function FactionCurrencyRequests({
    factionId,
    hasCurrency,
    onChanged,
}: {
    factionId: string;
    hasCurrency: boolean;
    onChanged: () => void;
}) {
    const { requests, refresh } = useFactionLinkRequests(factionId);
    const { currencies } = useCurrencies(!hasCurrency);
    const actions = useCurrencyLinkActions();
    const [wanted, setWanted] = useState("");

    const asked = new Set(requests.map((r) => r.currency_id));
    const choices = currencies.filter((c) => !asked.has(c.currency_id));

    const after = async (done: Promise<boolean>) => {
        if (await done) {
            refresh();
            onChanged();
        }
    };

    const ask = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!wanted) return;
        await after(actions.request(Number(wanted)));
        setWanted("");
    };

    if (hasCurrency && requests.length === 0) return null;

    return (
        <div className="info-values">
            {requests.map((r) => (
                <div className="info-row" key={r.request_id}>
                    <span className="info-label">
                        {r.kind === "INVITATION"
                            ? `La monnaie « ${r.currency_name} » est proposée à votre faction`
                            : `Demande en attente pour la monnaie « ${r.currency_name} »`}
                    </span>
                    <span className="info-value-field">
                        {r.kind === "INVITATION" ? (
                            <>
                                <button
                                    type="button"
                                    className="button"
                                    disabled={actions.loading || hasCurrency}
                                    title={
                                        hasCurrency
                                            ? "Quittez d'abord votre monnaie actuelle"
                                            : undefined
                                    }
                                    onClick={() =>
                                        after(actions.accept(r.request_id))
                                    }
                                >
                                    Accepter
                                </button>{" "}
                                <button
                                    type="button"
                                    className="button"
                                    disabled={actions.loading}
                                    onClick={() =>
                                        after(actions.refuse(r.request_id))
                                    }
                                >
                                    Refuser
                                </button>
                            </>
                        ) : (
                            <button
                                type="button"
                                className="button"
                                disabled={actions.loading}
                                onClick={() =>
                                    after(actions.withdraw(r.request_id))
                                }
                            >
                                Retirer la demande
                            </button>
                        )}
                    </span>
                </div>
            ))}
            {!hasCurrency && choices.length > 0 && (
                <form className="info-row" onSubmit={ask}>
                    <label>
                        Utiliser une monnaie existante{" "}
                        <select
                            value={wanted}
                            onChange={(e) => setWanted(e.target.value)}
                        >
                            <option value="">Choisir une monnaie...</option>
                            {choices.map((c) => (
                                <option
                                    key={c.currency_id}
                                    value={c.currency_id}
                                >
                                    {c.name}
                                    {c.symbol ? ` (${c.symbol})` : ""}
                                </option>
                            ))}
                        </select>
                    </label>
                    <button
                        type="submit"
                        className="button"
                        disabled={actions.loading || !wanted}
                    >
                        Demander
                    </button>
                </form>
            )}
            {actions.error && <p role="alert">{actions.error}</p>}
        </div>
    );
}
