import { useNewCurrency } from "../hooks/factioncurrency";

import "../../../assets/css/components/modals.css";
import "../../../assets/css/components/buttons.css";

export function NewCurrency() {
    const { form, loading, message, onSubmit, isOpen, setIsOpen } =
        useNewCurrency();

    const {
        register,
        formState: { errors },
    } = form;

    return (
        <div className="info-values">
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
                        <form onSubmit={onSubmit}>
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
