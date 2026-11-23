import React, { useState } from "react";
import { useAcceptOffer } from "../../hooks/offers/acceptoffer";
import { useMe } from "../../hooks/users/me";
import { useRole } from "../../hooks/factions/role";
import type { OfferTypeLiteral } from "../../types/offers";

interface AcceptOfferButtonProps {
    offerId: number;
    offerQuantity: number;
    // A BUY offer is accepted by selling to its author, a SELL one by buying
    offerType: OfferTypeLiteral;
    offerUserId?: number | null;
    offerFactionId?: number | null;
    onAccepted?: () => void;
}

export function AcceptOfferButton({
    offerId,
    offerQuantity,
    offerType,
    offerUserId,
    offerFactionId,
    onAccepted,
}: AcceptOfferButtonProps) {
    const { user } = useMe();
    const { role } = useRole(user?.role_id ?? null);
    const { acceptOffer, loading, message, error } = useAcceptOffer();

    const [isOpen, setIsOpen] = useState(false);
    const [quantity, setQuantity] = useState<number>(offerQuantity);
    const [chosenBuyFor, setBuyFor] = useState<"self" | "faction">("self");

    const quantityValid =
        Number.isInteger(quantity) &&
        quantity >= 1 &&
        quantity <= offerQuantity;

    const cantBuySelf = offerUserId === user?.user_id;

    const cantBuyFaction =
        !user?.faction_id ||
        !role?.accept_offers ||
        (offerFactionId && offerFactionId === user.faction_id);
    // Only show the "Acheter pour" section if there is a *choice* (both available)
    const hasChoice = !cantBuySelf && !cantBuyFaction;

    // The choice only counts when both are allowed; otherwise the allowed one
    // is used (if both are forbidden, "self" stays and submit is blocked).
    // Derived rather than reset in an effect, so it also follows the rules
    // when the user or their role finishes loading after the modal opened.
    const buyFor: "self" | "faction" = hasChoice
        ? chosenBuyFor
        : cantBuySelf && !cantBuyFaction
          ? "faction"
          : "self";

    // Each opening starts from the defaults
    const openModal = () => {
        setQuantity(offerQuantity);
        setBuyFor("self");
        setIsOpen(true);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // Guard (shouldn't happen since UI prevents choosing a forbidden option)
        if (buyFor === "faction" && !user?.faction_id) return;
        if (buyFor === "self" && cantBuySelf) return;
        if (!quantityValid) return;

        const payload = {
            quantity,
            buyer_user_id: buyFor === "self" ? user?.user_id : undefined,
            buyer_faction_id:
                buyFor === "faction" ? user?.faction_id : undefined,
        };

        const acceptedOffer = await acceptOffer(offerId, payload);

        if (acceptedOffer) {
            onAccepted?.();
            setIsOpen(false);
        }
    };

    return (
        <div>
            <button
                type="button"
                className="button"
                onClick={openModal}
            >
                Accepter
            </button>

            {isOpen && (
                <div
                    className="modal-container"
                    onClick={() => setIsOpen(false)}
                >
                    <div onClick={(e) => e.stopPropagation()} className="modal">
                        <h2>Accepter l'offre</h2>
                        <form onSubmit={handleSubmit}>
                            <div className="modal-field">
                                <label className="field-head">
                                    Quantité (max {offerQuantity})
                                </label>
                                <input
                                    type="number"
                                    min={1}
                                    max={offerQuantity}
                                    value={quantity}
                                    onChange={(e) =>
                                        setQuantity(
                                            Math.min(
                                                Number(e.target.value || 0),
                                                offerQuantity,
                                            ),
                                        )
                                    }
                                />
                            </div>

                            {/* Only show choice if both options are allowed */}
                            {hasChoice && (
                                <div className="modal-field">
                                    <label className="field-head">
                                        {offerType === "BUY"
                                            ? "Vendre pour"
                                            : "Acheter pour"}
                                    </label>
                                    <div
                                        style={{
                                            display: "flex",
                                            gap: "2em",
                                            flexDirection: "row",
                                            justifyContent: "center",
                                        }}
                                    >
                                        {!cantBuySelf && (
                                            <label>
                                                <input
                                                    type="radio"
                                                    value="self"
                                                    checked={buyFor === "self"}
                                                    onChange={() =>
                                                        setBuyFor("self")
                                                    }
                                                />{" "}
                                                Moi-même
                                            </label>
                                        )}

                                        {!cantBuyFaction && (
                                            <label>
                                                <input
                                                    type="radio"
                                                    value="faction"
                                                    checked={
                                                        buyFor === "faction"
                                                    }
                                                    onChange={() =>
                                                        setBuyFor("faction")
                                                    }
                                                />{" "}
                                                Ma faction
                                            </label>
                                        )}
                                    </div>
                                </div>
                            )}

                            <div className="modal-buttons">
                                <button
                                    type="submit"
                                    disabled={loading || !quantityValid}
                                    style={{
                                        flex: 1,
                                        backgroundColor: loading
                                            ? "#555"
                                            : "#4CAF50",
                                        padding: "10px 20px",
                                        border: "none",
                                        borderRadius: "6px",
                                        color: "white",
                                        cursor: loading
                                            ? "not-allowed"
                                            : "pointer",
                                    }}
                                >
                                    {loading ? "Traitement..." : "Confirmer"}
                                </button>

                                <button
                                    type="button"
                                    onClick={() => setIsOpen(false)}
                                    style={{
                                        flex: 1,
                                        backgroundColor: "#d9534f",
                                        padding: "10px 20px",
                                        border: "none",
                                        borderRadius: "6px",
                                        color: "white",
                                        cursor: "pointer",
                                    }}
                                >
                                    Annuler
                                </button>
                            </div>
                        </form>

                        {(message || error) && (
                            <p
                                style={{
                                    marginTop: "10px",
                                    color: error ? "red" : "green",
                                }}
                            >
                                {error || message}
                            </p>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
