import { useNewOffer } from "../hooks/offers";
import { useMe } from "../hooks/me";
import { useRole } from "../hooks/role";

export function NewOffer() {
    const { user } = useMe();
    const { role } = useRole(user?.role_id ?? null);

    const {
        form,
        loading,
        message,
        onSubmit,
        isOpen,
        setIsOpen,
        forFaction,
        setForFaction,
    } = useNewOffer();

    const {
        register,
        formState: { errors },
    } = form;

    return (
        <div>
            <div className="button" onClick={() => setIsOpen(true)}>
                Créer une offre
            </div>

            {isOpen && (
                <div
                    className="modal-container"
                    onClick={() => setIsOpen(false)}
                >
                    <div onClick={(e) => e.stopPropagation()} className="modal">
                        <h2>Créer une offre</h2>
                        <form onSubmit={onSubmit}>
                            <div className="modal-field">
                                <label>Type</label>
                                <select {...register("offer_type")}>
                                    <option value="">
                                        Séléctioner un type
                                    </option>
                                    <option value="BUY">Acheter</option>
                                    <option value="SELL">Vendre</option>
                                </select>
                                {errors.offer_type && (
                                    <p>{errors.offer_type.message}</p>
                                )}
                            </div>

                            <div className="modal-field">
                                <label>Description</label>
                                <input
                                    type="text"
                                    {...register("item_description")}
                                />
                                {errors.item_description && (
                                    <p>{errors.item_description.message}</p>
                                )}
                            </div>

                            <div className="modal-field">
                                <label>Monaie</label>
                                <input
                                    type="text"
                                    {...register("currency_name")}
                                />
                                {errors.currency_name && (
                                    <p>{errors.currency_name.message}</p>
                                )}
                            </div>

                            <div className="modal-field">
                                <label>Prix par unité</label>
                                <input
                                    type="number"
                                    step="1"
                                    {...register("price_per_unit")}
                                />
                                {errors.price_per_unit && (
                                    <p>{errors.price_per_unit.message}</p>
                                )}
                            </div>

                            <div className="modal-field">
                                <label>Quantité</label>
                                <input
                                    type="number"
                                    {...register("quantity")}
                                />
                                {errors.quantity && (
                                    <p>{errors.quantity.message}</p>
                                )}
                            </div>

                            {role?.create_offers ? (
                                <div className="modal-field">
                                    <label>
                                        <input
                                            type="checkbox"
                                            checked={forFaction}
                                            onChange={(e) =>
                                                setForFaction(e.target.checked)
                                            }
                                        />
                                        Pour la faction
                                    </label>
                                </div>
                            ) : (
                                <></>
                            )}

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
