import { useState } from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";

import axios from "axios";
import * as yup from "yup";

import { useAuth } from "../../utils/authprovider";

import type { CurrencyType, CurrencyFormData } from "../../types/currency";

import "../../../assets/css/components/modals.css";
import "../../../assets/css/components/buttons.css";

import { useMe } from "../hooks/me";

const currencySchema = yup.object().shape({
    name: yup.string().required("Le nom de la monnaie est obligatoire"),
    symbol: yup.string().optional().nullable().default(null),
    total_in_circulation: yup
        .number()
        .typeError("Doit être un nombre")
        .min(0, "La quantité ne peut pas être négative")
        .required("La quantité en circulation est obligatoire"),
});

export function NewCurrency() {
    const { token } = useAuth() ?? {};

    const { user } = useMe();

    const [isOpen, setIsOpen] = useState<boolean>(false);
    const [loading, setLoading] = useState<boolean>(false);
    const [message, setMessage] = useState<string>("");

    const {
        register,
        handleSubmit,
        reset,
        formState: { errors },
    } = useForm<CurrencyFormData>({
        resolver: yupResolver(currencySchema),
    });

    const onSubmit = async (data: CurrencyFormData) => {
        setLoading(true);
        setMessage("");

        try {
            if (!token) {
                throw new Error(
                    "Vous devez être connecté pour créer une monnaie."
                );
            }

            console.log("ererezr");

            const payload = {
                ...data,
                faction_id: user?.faction_id,
            };

            const res = await axios.post<CurrencyType>(
                "http://localhost:8000/currencies/create",
                payload
            );

            setMessage(`✅ Monnaie "${res.data.name}" créée avec succès`);
            reset();
            setIsOpen(false);
            window.location.reload();
        } catch (error: any) {
            if (error.response?.status === 409) {
                setMessage(
                    "❌ Une monnaie avec ce nom ou symbole existe déjà."
                );
            } else {
                setMessage("❌ Erreur lors de la création de la monnaie.");
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <div className="button" onClick={() => setIsOpen(true)}>
                Créer une monnaie
            </div>

            {isOpen && (
                <div
                    className="modal-container"
                    onClick={() => setIsOpen(false)}
                >
                    <div onClick={(e) => e.stopPropagation()} className="modal">
                        <h2>Créer une monnaie</h2>
                        <form onSubmit={handleSubmit(onSubmit)}>
                            <div className="modal-field">
                                <label>Nom</label>
                                <input type="text" {...register("name")} />
                                {errors.name && <p>{errors.name.message}</p>}
                            </div>

                            <div className="modal-field">
                                <label>Symbole</label>
                                <input type="text" {...register("symbol")} />
                                {errors.symbol && (
                                    <p>{errors.symbol.message}</p>
                                )}
                            </div>

                            <div className="modal-field">
                                <label>Total en circulation</label>
                                <input
                                    type="number"
                                    {...register("total_in_circulation")}
                                />
                                {errors.total_in_circulation && (
                                    <p>{errors.total_in_circulation.message}</p>
                                )}
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
                                    {loading ? "Création..." : "Créer"}
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

                        {message && (
                            <p style={{ marginTop: "10px" }}>{message}</p>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
