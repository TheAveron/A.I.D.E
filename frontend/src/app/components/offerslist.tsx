import { NewOffer } from "./buttons/newoffer";
import { useOffersList } from "./hooks/offers";

import "../../assets/css/components/offers.css";
import "../../assets/css/components/tables.css";
import "../../assets/css/components/snippets.css";

function OfferList() {
    const { offers, loading, error } = useOffersList();

    return (
        <div className="snippet-container offers-container">
            <div className="offers-header">
                <h2>Liste des offres</h2>
                <NewOffer />
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Statut</th>
                        <th>Item</th>
                        <th>Quantité</th>
                        <th>Prix par unité</th>
                        <th>Création</th>
                    </tr>
                </thead>
                <tbody>
                    {!error ? (
                        !loading ? (
                            offers && offers.length > 0 ? (
                                offers.map((offer) => (
                                    <tr key={offer.offer_id}>
                                        <td>
                                            {offer.offer_type === "BUY"
                                                ? "Achat"
                                                : "Vente"}
                                        </td>
                                        <td>
                                            {offer.status === "OPEN"
                                                ? "Ouvert"
                                                : offer.status === "CLOSED"
                                                  ? "Complétée"
                                                  : "Annulée"}
                                        </td>
                                        <td>{offer.item_description}</td>
                                        <td>{offer.quantity}</td>
                                        <td>{offer.price_per_unit}</td>
                                        <td>
                                            {new Date(
                                                offer.created_at
                                            ).toLocaleDateString()}
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan={6}>Pas d'offre disponible.</td>
                                </tr>
                            )
                        ) : (
                            <tr>
                                <td colSpan={6}>Chargement des offres...</td>
                            </tr>
                        )
                    ) : (
                        <tr>
                            <td colSpan={6} style={{ color: "red" }}>
                                Erreur lors du chargement des offres.
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
}

export default OfferList;
