import { useState } from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import axios from "axios";
import * as yup from "yup";

import { useAuth } from "../../utils/authprovider";
import "../../../assets/css/components/modals.css";
import "../../../assets/css/components/buttons.css";
import { useMe } from "../hooks/me";

// Types matching OfferCreate
interface OfferFormData {
    offer_type: string;
    item_description: string;
    currency_name: string;
    price_per_unit: number;
    quantity: number;
    allowed_parties: string | null;
    user_id: number | null;
    faction_id: number | null;
}

// Validation schema
const offerSchema = yup.object().shape({
    offer_type: yup.string().required("Offer type is required"),
    item_description: yup
        .string()
        .required("Item description is required")
        .max(255, "Max 255 characters"),
    currency_name: yup.string().required("Currency name is required"),
    price_per_unit: yup
        .number()
        .typeError("Price must be a number")
        .positive("Price must be positive")
        .required("Price per unit is required"),
    quantity: yup
        .number()
        .typeError("Quantity must be a number")
        .integer("Quantity must be an integer")
        .positive("Quantity must be positive")
        .required("Quantity is required"),
    allowed_parties: yup.string().optional().nullable().default(null),
    user_id: yup.number().optional().nullable().default(null),
    faction_id: yup.number().optional().nullable().default(null),
});

export function NewOffer() {
    const { token } = useAuth() ?? {};
    const { user } = useMe() ?? {}; // expects { user_id, faction_id, ... }

    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState("");
    const [forFaction, setForFaction] = useState(false); // checkbox state

    const {
        register,
        handleSubmit,
        reset,
        formState: { errors },
    } = useForm<OfferFormData>({
        resolver: yupResolver(offerSchema),
    });

    const onSubmit = async (data: OfferFormData) => {
        setLoading(true);
        setMessage("");

        try {
            if (!token) {
                throw new Error("You must be logged in to create an offer.");
            }
            if (!user) {
                throw new Error("Unable to get user information.");
            }

            // Convert allowed_parties string to array of ints
            const allowedPartiesArray = data.allowed_parties
                ? data.allowed_parties
                      .split(",")
                      .map((id) => parseInt(id.trim()))
                      .filter((id) => !isNaN(id))
                : undefined;

            const payload: OfferFormData = {
                ...data,
                allowed_parties: null,
                user_id: forFaction ? null : user.user_id,
                faction_id: forFaction ? user.faction_id : null,
            };

            const res = await axios.post(
                "http://localhost:8000/offers/create",
                payload,
                { headers: { Authorization: `Bearer ${token}` } }
            );

            setMessage(
                `✅ Offer "${res.data.item_description}" created successfully`
            );
            reset();
            setForFaction(false);
            setIsOpen(false);
            window.location.reload();
        } catch (error: any) {
            if (error.response?.status === 409) {
                setMessage("❌ An offer with these details already exists.");
            } else {
                setMessage("❌ Error creating offer.");
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <div className="button" onClick={() => setIsOpen(true)}>
                Create Offer
            </div>

            {isOpen && (
                <div
                    className="modal-container"
                    onClick={() => setIsOpen(false)}
                >
                    <div onClick={(e) => e.stopPropagation()} className="modal">
                        <h2>Create a New Offer</h2>
                        <form onSubmit={handleSubmit(onSubmit)}>
                            <div className="modal-field">
                                <label>Offer Type</label>
                                <select {...register("offer_type")}>
                                    <option value="">Select type</option>
                                    <option value="BUY">Buy</option>
                                    <option value="SELL">Sell</option>
                                </select>
                                {errors.offer_type && (
                                    <p>{errors.offer_type.message}</p>
                                )}
                            </div>

                            <div className="modal-field">
                                <label>Item Description</label>
                                <input
                                    type="text"
                                    {...register("item_description")}
                                />
                                {errors.item_description && (
                                    <p>{errors.item_description.message}</p>
                                )}
                            </div>

                            <div className="modal-field">
                                <label>Currency Name</label>
                                <input
                                    type="text"
                                    {...register("currency_name")}
                                />
                                {errors.currency_name && (
                                    <p>{errors.currency_name.message}</p>
                                )}
                            </div>

                            <div className="modal-field">
                                <label>Price Per Unit</label>
                                <input
                                    type="number"
                                    step="0.01"
                                    {...register("price_per_unit")}
                                />
                                {errors.price_per_unit && (
                                    <p>{errors.price_per_unit.message}</p>
                                )}
                            </div>

                            <div className="modal-field">
                                <label>Quantity</label>
                                <input
                                    type="number"
                                    {...register("quantity")}
                                />
                                {errors.quantity && (
                                    <p>{errors.quantity.message}</p>
                                )}
                            </div>

                            <div className="modal-field">
                                <label>
                                    <input
                                        type="checkbox"
                                        checked={forFaction}
                                        onChange={(e) =>
                                            setForFaction(e.target.checked)
                                        }
                                    />{" "}
                                    For Faction
                                </label>
                            </div>

                            <div className="modal-buttons">
                                <button
                                    type="submit"
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
                                    {loading ? "Creating..." : "Create"}
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
                                    Cancel
                                </button>
                            </div>
                        </form>

                        {message && (
                            <p style={{ marginTop: "10px" }}>{message}</p>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
