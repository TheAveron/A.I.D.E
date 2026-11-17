import { useState } from "react";
import axios from "axios";
import { useAuth } from "../../utils/authcontext";
import { getErrorMessage } from "../../utils/apierror";
import type { OfferAcceptPayload, OfferResponse } from "../../types/offers";

export function useAcceptOffer() {
    const { token } = useAuth();

    const [loading, setLoading] = useState<boolean>(false);
    const [message, setMessage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const acceptOffer = async (
        offerId: number,
        payload: OfferAcceptPayload,
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
            );

            setMessage("✅ Offre acceptée avec succès !");
            return res.data;
        } catch (error: unknown) {
            setError(`❌ ${getErrorMessage(error, "Erreur serveur")}`);
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
