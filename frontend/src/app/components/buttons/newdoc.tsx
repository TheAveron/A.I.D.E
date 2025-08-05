import { useState } from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import axios from "axios";
import * as yup from "yup";

import { useAuth } from "../../utils/authprovider";
import "../../../assets/css/components/modals.css";
import "../../../assets/css/components/buttons.css";

export type DocumentFormData = {
    title: string;
    content: string;
};

const documentSchema = yup.object().shape({
    title: yup
        .string()
        .required("Le titre du document est obligatoire")
        .max(30, "Le titre ne peut pas dépasser 30 caractères")
        .min(5, "Le titre ne peut pas faire moins de 5 caractères"),
    content: yup.string().required("Le contenu du document est obligatoire"),
});

export function NewDocument() {
    const { token } = useAuth() ?? {};

    const [isOpen, setIsOpen] = useState<boolean>(false);
    const [loading, setLoading] = useState<boolean>(false);
    const [message, setMessage] = useState<string>("");

    const {
        register,
        handleSubmit,
        reset,
        formState: { errors },
    } = useForm<DocumentFormData>({
        resolver: yupResolver(documentSchema),
    });

    const onSubmit = async (data: DocumentFormData) => {
        setLoading(true);
        setMessage("");

        try {
            if (!token) {
                throw new Error(
                    "Vous devez être connecté pour créer un document."
                );
            }
            const res = await axios.post(
                "http://localhost:8000/documents/create",
                data
            );

            setMessage(`✅ Document "${res.data.title}" créé avec succès`);
            reset();
            setIsOpen(false);
            window.location.reload();
        } catch (error: any) {
            if (error.response?.status === 409) {
                setMessage("❌ Un document avec ce titre existe déjà.");
            } else {
                setMessage("❌ Erreur lors de la création du document.");
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <div className="button" onClick={() => setIsOpen(true)}>
                Créer un document
            </div>

            {isOpen && (
                <div
                    className="modal-container"
                    onClick={() => setIsOpen(false)}
                >
                    <div onClick={(e) => e.stopPropagation()} className="modal">
                        <h2>Créer un document</h2>
                        <form onSubmit={handleSubmit(onSubmit)}>
                            <div className="modal-field">
                                <label>Titre</label>
                                <input type="text" {...register("title")} />
                                {errors.title && <p>{errors.title.message}</p>}
                            </div>

                            <div className="modal-field">
                                <label>Contenu (Markdown)</label>
                                <textarea
                                    {...register("content")}
                                    rows={10}
                                    style={{ fontFamily: "monospace" }}
                                />
                                {errors.content && (
                                    <p>{errors.content.message}</p>
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
