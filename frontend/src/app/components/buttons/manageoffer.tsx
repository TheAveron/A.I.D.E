import axios from "axios";
import { useState, type FormEvent } from "react";

import { getErrorMessage } from "../../utils/apierror";
import type { OfferType } from "../../types/offers";

const INT32_MAX = 2147483647;

/**
 * Change the price and quantity of an open offer, or cancel it. The server
 * keeps a history entry for both.
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
    const unchanged =
        priceValue === offer.price_per_unit && quantityValue === offer.quantity;

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
        if (!valid || unchanged) return;
        const changes: { price_per_unit?: number; quantity?: number } = {};
        if (priceValue !== offer.price_per_unit)
            changes.price_per_unit = priceValue;
        if (quantityValue !== offer.quantity) changes.quantity = quantityValue;
        void run(() => axios.put(`/offers/update/${offer.offer_id}`, changes));
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
                    <button
                        type="submit"
                        className="button"
                        disabled={loading || !valid || unchanged}
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
                        onClick={() => setEditing(true)}
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
