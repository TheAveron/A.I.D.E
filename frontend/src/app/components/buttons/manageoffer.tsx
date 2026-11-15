import axios from "axios";
import { useState, type FormEvent } from "react";

import { getErrorMessage } from "../../utils/apierror";
import type { OfferType } from "../../types/offers";
import { useFactions } from "../hooks/factions";
import {
    factionNamesText,
    resolveAudience,
    userNamesText,
} from "../../utils/audience";

const sameIds = (a: number[] | null, b: number[] | null) =>
    [...(a ?? [])].sort((x, y) => x - y).join() ===
    [...(b ?? [])].sort((x, y) => x - y).join();

const INT32_MAX = 2147483647;

/**
 * Change the price, quantity and audience (users and factions an offer is
 * reserved to; empty: everybody) of an open offer, or cancel it. The server
 * keeps a history entry for each.
 */
export function ManageOfferButtons({
    offer,
    onChanged,
}: {
    offer: OfferType;
    onChanged: () => void;
}) {
    const [editing, setEditing] = useState(false);
    const [price, setPrice] = useState(String(offer.price_per_unit));
    const [quantity, setQuantity] = useState(String(offer.quantity));
    const [audienceUsers, setAudienceUsers] = useState("");
    const [audienceFactions, setAudienceFactions] = useState("");
    const { factions } = useFactions();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const priceValue = Number(price);
    const quantityValue = Number(quantity);
    const valid =
        price.trim() !== "" &&
        quantity.trim() !== "" &&
        Number.isFinite(priceValue) &&
        priceValue > 0 &&
        Number.isInteger(quantityValue) &&
        quantityValue > 0 &&
        quantityValue <= INT32_MAX;

    const open = async () => {
        setLoading(true);
        setAudienceUsers(await userNamesText(offer.allowed_user_ids));
        setAudienceFactions(
            factionNamesText(offer.allowed_faction_ids, factions),
        );
        setLoading(false);
        setEditing(true);
    };

    const run = async (action: () => Promise<unknown>) => {
        setLoading(true);
        setError("");
        try {
            await action();
            setEditing(false);
            onChanged();
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setLoading(false);
        }
    };

    const save = (event: FormEvent) => {
        event.preventDefault();
        if (!valid) return;
        void run(async () => {
            const { userIds, factionIds } = await resolveAudience(
                audienceUsers,
                audienceFactions,
                factions,
            );
            const changes: {
                price_per_unit?: number;
                quantity?: number;
                allowed_user_ids?: number[] | null;
                allowed_faction_ids?: number[] | null;
            } = {};
            if (priceValue !== offer.price_per_unit)
                changes.price_per_unit = priceValue;
            if (quantityValue !== offer.quantity)
                changes.quantity = quantityValue;
            if (!sameIds(userIds, offer.allowed_user_ids))
                changes.allowed_user_ids = userIds;
            if (!sameIds(factionIds, offer.allowed_faction_ids))
                changes.allowed_faction_ids = factionIds;
            if (Object.keys(changes).length === 0) return;
            await axios.put(`/offers/update/${offer.offer_id}`, changes);
        });
    };

    const cancel = () => {
        if (!window.confirm("Annuler cette offre ?")) return;
        void run(() => axios.delete(`/offers/delete/${offer.offer_id}`));
    };

    return (
        <>
            {editing ? (
                <form onSubmit={save}>
                    <label>
                        Prix{" "}
                        <input
                            type="number"
                            min="0"
                            step="any"
                            value={price}
                            onChange={(e) => setPrice(e.target.value)}
                        />
                    </label>{" "}
                    <label>
                        Quantité{" "}
                        <input
                            type="number"
                            min="1"
                            step="1"
                            value={quantity}
                            onChange={(e) => setQuantity(e.target.value)}
                        />
                    </label>{" "}
                    <br />
                    <label>
                        Réservée aux utilisateurs{" "}
                        <input
                            type="text"
                            placeholder="noms séparés par des virgules"
                            value={audienceUsers}
                            onChange={(e) => setAudienceUsers(e.target.value)}
                        />
                    </label>{" "}
                    <label>
                        et aux factions{" "}
                        <input
                            type="text"
                            placeholder="noms séparés par des virgules"
                            value={audienceFactions}
                            onChange={(e) =>
                                setAudienceFactions(e.target.value)
                            }
                        />
                    </label>{" "}
                    <button
                        type="submit"
                        className="button"
                        disabled={loading || !valid}
                    >
                        Enregistrer
                    </button>{" "}
                    <button
                        type="button"
                        className="button"
                        disabled={loading}
                        onClick={() => setEditing(false)}
                    >
                        Fermer
                    </button>
                </form>
            ) : (
                <>
                    <button
                        type="button"
                        className="button"
                        disabled={loading}
                        onClick={open}
                    >
                        Modifier
                    </button>{" "}
                    <button
                        type="button"
                        className="button"
                        disabled={loading}
                        onClick={cancel}
                    >
                        Annuler
                    </button>
                </>
            )}
            {error && <p role="alert">{error}</p>}
        </>
    );
}
