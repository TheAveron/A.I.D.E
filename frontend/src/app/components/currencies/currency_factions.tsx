import { useState } from "react";
import { Link } from "react-router";

import {
    useCurrencyLinkActions,
    useCurrencyLinkRequests,
} from "../../hooks/currencies/currency_links";
import { useFactions } from "../../hooks/factions/factions";
import type { CurrencyType } from "../../types/currency";

const NO_FACTION_NAME = "Sans Faction";

/**
 * The factions using a currency. Its managers (an issuer's holders of
 * manage_funds, money admins) make factions issuers or not, remove them,
 * propose the currency to others and answer the requests; a faction's own
 * holders of manage_funds may have it leave. The last issuer stays: the
 * server refuses, and the buttons are not offered.
 */
export function CurrencyFactions({
    currency,
    viewerFactionId,
    viewerHoldsFunds,
    onChanged,
}: {
    currency: CurrencyType;
    viewerFactionId: number | null;
    viewerHoldsFunds: boolean;
    onChanged: () => void;
}) {
    const manager = currency.can_manage;
    const actions = useCurrencyLinkActions();
    const { requests, refresh: refreshRequests } = useCurrencyLinkRequests(
        manager ? currency.currency_id : null,
    );
    const { factions } = useFactions();
    const [inviteId, setInviteId] = useState("");

    const issuers = currency.factions.filter((f) => f.is_issuer).length;
    const using = new Set(currency.factions.map((f) => f.faction_id));
    const invited = new Set(requests.map((r) => r.faction_id));
    const candidates = (factions ?? []).filter(
        (f) =>
            !using.has(f.faction_id) &&
            !invited.has(f.faction_id) &&
            f.name !== NO_FACTION_NAME,
    );

    const after = async (done: Promise<boolean>) => {
        if (await done) {
            refreshRequests();
            onChanged();
        }
    };

    const invite = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!inviteId) return;
        await after(actions.invite(currency.currency_id, Number(inviteId)));
        setInviteId("");
    };

    const leave = (factionId: number, name: string) => {
        if (
            !window.confirm(
                `Retirer ${name} de la monnaie « ${currency.name} » ?`,
            )
        ) {
            return;
        }
        after(actions.removeFaction(currency.currency_id, factionId));
    };

    return (
        <div className="info-values">
            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Faction</th>
                            <th>Rôle</th>
                            <th>Depuis</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {currency.factions.map((f) => {
                            const lastIssuer = f.is_issuer && issuers <= 1;
                            const own = f.faction_id === viewerFactionId;
                            const canRemove =
                                !lastIssuer &&
                                (manager || (own && viewerHoldsFunds));
                            const name = f.faction_name ?? `#${f.faction_id}`;
                            return (
                                <tr key={f.faction_id}>
                                    <td>
                                        <Link to={`/faction/${f.faction_id}`}>
                                            {name}
                                        </Link>
                                    </td>
                                    <td>
                                        {f.is_issuer
                                            ? "Émettrice"
                                            : "Utilisatrice"}
                                    </td>
                                    <td>
                                        {new Date(
                                            f.joined_at,
                                        ).toLocaleDateString()}
                                    </td>
                                    <td>
                                        {manager && !lastIssuer && (
                                            <button
                                                type="button"
                                                className="button"
                                                disabled={actions.loading}
                                                onClick={() =>
                                                    after(
                                                        actions.setIssuer(
                                                            currency.currency_id,
                                                            f.faction_id,
                                                            !f.is_issuer,
                                                        ),
                                                    )
                                                }
                                            >
                                                {f.is_issuer
                                                    ? "Retirer l'émission"
                                                    : "Rendre émettrice"}
                                            </button>
                                        )}{" "}
                                        {canRemove && (
                                            <button
                                                type="button"
                                                className="button"
                                                disabled={actions.loading}
                                                onClick={() =>
                                                    leave(f.faction_id, name)
                                                }
                                            >
                                                {own && !manager
                                                    ? "Quitter la monnaie"
                                                    : "Retirer"}
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            {manager && (
                <>
                    <form className="info-row" onSubmit={invite}>
                        <label>
                            Proposer la monnaie à une faction{" "}
                            <select
                                value={inviteId}
                                onChange={(e) => setInviteId(e.target.value)}
                            >
                                <option value="">Choisir une faction...</option>
                                {candidates.map((f) => (
                                    <option
                                        key={f.faction_id}
                                        value={f.faction_id}
                                    >
                                        {f.name}
                                    </option>
                                ))}
                            </select>
                        </label>
                        <button
                            type="submit"
                            className="button"
                            disabled={actions.loading || !inviteId}
                        >
                            Proposer
                        </button>
                    </form>
                    {requests.length > 0 && (
                        <div className="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Faction</th>
                                        <th>En attente</th>
                                        <th>Date</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {requests.map((r) => (
                                        <tr key={r.request_id}>
                                            <td>
                                                <Link
                                                    to={`/faction/${r.faction_id}`}
                                                >
                                                    {r.faction_name ??
                                                        `#${r.faction_id}`}
                                                </Link>
                                            </td>
                                            <td>
                                                {r.kind === "REQUEST"
                                                    ? "Demande à utiliser la monnaie"
                                                    : "Proposition envoyée"}
                                            </td>
                                            <td>
                                                {new Date(
                                                    r.created_at,
                                                ).toLocaleDateString()}
                                            </td>
                                            <td>
                                                {r.kind === "REQUEST" ? (
                                                    <>
                                                        <button
                                                            type="button"
                                                            className="button"
                                                            disabled={
                                                                actions.loading
                                                            }
                                                            onClick={() =>
                                                                after(
                                                                    actions.accept(
                                                                        r.request_id,
                                                                    ),
                                                                )
                                                            }
                                                        >
                                                            Accepter
                                                        </button>{" "}
                                                        <button
                                                            type="button"
                                                            className="button"
                                                            disabled={
                                                                actions.loading
                                                            }
                                                            onClick={() =>
                                                                after(
                                                                    actions.refuse(
                                                                        r.request_id,
                                                                    ),
                                                                )
                                                            }
                                                        >
                                                            Refuser
                                                        </button>
                                                    </>
                                                ) : (
                                                    <button
                                                        type="button"
                                                        className="button"
                                                        disabled={
                                                            actions.loading
                                                        }
                                                        onClick={() =>
                                                            after(
                                                                actions.withdraw(
                                                                    r.request_id,
                                                                ),
                                                            )
                                                        }
                                                    >
                                                        Annuler
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </>
            )}
            {actions.error && <p role="alert">{actions.error}</p>}
        </div>
    );
}
