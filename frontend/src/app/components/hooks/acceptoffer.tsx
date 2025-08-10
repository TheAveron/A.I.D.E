import { useState } from "react";
import axios from "axios";
import { useAuth } from "../../utils/authprovider";
import type { OfferAcceptPayload, OfferResponse } from "../../types/offers";

export function useAcceptOffer() {
    const { token } = useAuth();

    const [loading, setLoading] = useState<boolean>(false);
    const [message, setMessage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const acceptOffer = async (
        offerId: number,
        payload: OfferAcceptPayload
    ) => {
        if (!token) {
            setError("Vous devez être connecté pour accepter une offre.");
            return;
        }

        setLoading(true);
        setMessage(null);
        setError(null);

        try {
            const res = await axios.post<OfferResponse>(
                `/offers/accept/${offerId}`,
                payload,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            setMessage("✅ Offre acceptée avec succès !");
            return res.data;
        } catch (error: any) {
            if (error.response) {
                setError(`❌ ${error.response.data.detail}`);
            } else {
                setError("❌ Erreur lors de l'acceptation de l'offre.");
            }
        } finally {
            setLoading(false);
        }
    };

    return {
        acceptOffer,
        loading,
        message,
        error,
    };
}
