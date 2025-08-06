import { useNewFaction } from "../hooks/faction";

import "../../../assets/css/components/modals.css";
import "../../../assets/css/components/buttons.css";

export function NewFaction() {
    const { form, loading, message, onSubmit, isOpen, setIsOpen } =
        useNewFaction();

    const {
        register,
        formState: { errors },
    } = form;

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
                        <form onSubmit={onSubmit}>
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
