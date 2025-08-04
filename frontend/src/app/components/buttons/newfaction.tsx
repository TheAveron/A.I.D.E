import { useState } from "react";
import { useAuth } from "../../utils/authprovider";
import axios from "axios";

import { useForm } from "react-hook-form";
import * as yup from "yup";

import { yupResolver } from "@hookform/resolvers/yup";
import { useMe } from "../hooks/me";

import "../../../assets/css/components/modals.css";
import "../../../assets/css/components/buttons.css";

type FactionFormData = {
    name: string;
    description: string | null;
    is_approved: boolean;
};

interface FactionResponse {
    faction_id: number;
    name: string;
    description?: string | null;
    currency_name?: string | null;
}

const factionSchema = yup.object().shape({
    name: yup.string().required("Le nom de la faction est obligatoire"),
    description: yup
        .string()
        .max(500, "La description est trop longue")
        .nullable()
        .default(null),

    is_approved: yup.boolean().default(false),
});

export function NewFaction() {
    const { token } = useAuth() ?? {};

    const { user } = useMe();

    if (!user) {
        return <></>;
    }

    if (user.faction_id) {
        return <></>;
    }

    const [isOpen, setIsOpen] = useState<boolean>(false);
    const [loading, setLoading] = useState<boolean>(false);
    const [message, setMessage] = useState<string>("");

    const {
        register,
        handleSubmit,
        reset,
        formState: { errors },
    } = useForm<FactionFormData>({
        resolver: yupResolver(factionSchema),
    });

    const onSubmit = async (data: FactionFormData) => {
        setLoading(true);
        setMessage("");

        try {
            if (!token) {
                throw new Error(
                    "Vous devez être connecté pour créer une faction."
                );
            }

            const payload = {
                ...data,
                is_approved: false, // default for new factions
            };

            const res = await axios.post<FactionResponse>(
                "http://localhost:8000/factions/create",
                payload
            );

            setMessage(`✅ Faction "${res.data.name}" créée avec succès`);
            reset();
            setIsOpen(false);

            window.location.reload();
        } catch (error: any) {
            if (error.response?.status === 409) {
                setMessage("❌ Une faction avec ce nom existe déjà.");
            } else {
                setMessage("❌ Erreur lors de la création de la faction.");
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <div className="button" onClick={() => setIsOpen(true)}>
                Créer une faction
            </div>

            {isOpen && (
                <div
                    className="modal-container"
                    onClick={() => setIsOpen(false)}
                >
                    <div onClick={(e) => e.stopPropagation()} className="modal">
                        <h2>Créer une faction</h2>
                        <form onSubmit={handleSubmit(onSubmit)}>
                            <div className="modal-field">
                                <label>Nom</label>
                                <input type="text" {...register("name")} />
                                {errors.name && <p>{errors.name.message}</p>}
                            </div>

                            <div className="modal-field">
                                <label>Description</label>
                                <textarea {...register("description")} />
                                {errors.description && (
                                    <p>{errors.description.message}</p>
                                )}
                            </div>

                            <div className="modal-buttons">
                                <button
                                    type="submit"
                                    disabled={loading}
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
