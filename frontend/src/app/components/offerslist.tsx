import { useEffect, useState } from "react";
import type { OfferType } from "../types/offers";
import axios from "axios";

import "../../assets/css/components/offers.css";
import "../../assets/css/components/tables.css";
import "../../assets/css/components/snippets.css";

function OfferList() {
    const [offers, setOffers] = useState<OfferType[] | null>(null);
    const [loading, setLoading] = useState(true);

    // Fetch offers from API
    useEffect(() => {
        const fetchOffers = async () => {
            try {
                const res = await axios.get<OfferType[]>(
                    "http://127.0.0.1:8000/offers/list"
                );
                setOffers(res.data);
            } finally {
                setLoading(false);
            }
        };

        fetchOffers();
    }, []);

    /*useEffect(() => {
        if (!offers || offers.length === 0) {
            setOffers([
                {
                    offer_type: "BUY",
                    item_description: "Test offer",
                    currency: "Diamond",
                    price_per_unit: 0,
                    quantity: 0,
                    allowed_parties: [0],
                    offer_id: 0,
                    user_id: 0,
                    faction_id: 0,
                    status: "OPEN",
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                },
            ]);
        }
    }, [offers]);*/

    if (loading) {
        return <p>Chargement...</p>;
    }

    return (
        <div className="snippet-container offers-container">
            <div className="offers-header">
                <h2>Liste des offres</h2>
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
                    {offers && offers.length > 0 ? (
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
                    )}
                </tbody>
            </table>
        </div>
    );
}

export default OfferList;
