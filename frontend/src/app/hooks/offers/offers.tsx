import { useState, useMemo } from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";

import * as yup from "yup";
import axios from "axios";

import { useAuth } from "../../utils/authcontext";
import { getErrorMessage } from "../../utils/apierror";
import { useApiGet } from "../../utils/useapiget";
import { useMe } from "../users/me";
import { useFactions } from "../factions/factions";
import { resolveAudience } from "../../utils/audience";
import { fromLocalInput } from "../../utils/expiry";

import type {
    OfferCreate as OfferForm,
    OffersHook,
    OfferType,
    OfferCreateData,
    OfferFormHook,
    OfferTypeLiteral,
    OfferHook,
} from "../../types/offers";

export const offerSchema = yup.object().shape({
    offer_type: yup
        .mixed<OfferTypeLiteral>()
        .oneOf(["BUY", "SELL"], "Choisissez achat ou vente")
        .required("Choisissez achat ou vente"),
    item_description: yup
        .string()
        .required("La description est obligatoire")
        .max(255, "255 caractères au maximum"),
    currency_name: yup.string().required("Choisissez une monnaie"),
    price_per_unit: yup
        .number()
        .typeError("Le prix doit être un nombre")
        .positive("Le prix doit être positif")

        .max(1e12, "Le prix est trop élevé")
        .required("Le prix par unité est obligatoire"),
    quantity: yup
        .number()
        .typeError("La quantité doit être un nombre")
        .integer("La quantité doit être un nombre entier")
        .positive("La quantité doit être positive")
        .max(2147483647, "La quantité est trop élevée")
        .required("La quantité est obligatoire"),
});

export function useOffer(offer_id?: number): OfferHook {
    const { data, loading, error } = useApiGet<OfferType>(
        offer_id != null ? `/offers/detail/${offer_id}` : null,
        "Impossible de charger l'offre",
    );

    return { offer: data, loading, error };
}

// The server returns 50 offers unless asked for more (up to 200), newest first.
const MAX_OFFERS = "200";

export interface OffersFilters {
    currency?: string;
    status?: string;
    offerType?: string;
    search?: string;
    minPrice?: string;
    maxPrice?: string;
    userId?: string | null;
    factionId?: string | null;
}

export function useOffersList(filters: OffersFilters): OffersHook {
    const {
        currency,
        status,
        offerType,
        search,
        minPrice,
        maxPrice,
        userId,
        factionId,
    } = filters;
    const query = useMemo(() => {
        const params = new URLSearchParams({ limit: MAX_OFFERS });
        if (status) params.append("status", status);
        if (currency) params.append("currency", currency);
        if (offerType) params.append("offer_type", offerType);
        if (search?.trim()) params.append("q", search.trim().slice(0, 100));
        // Filtered by the server: filtering the 200 newest offers here would
        // hide the older ones.
        if (minPrice && Number(minPrice) >= 0)
            params.append("min_price", minPrice);
        if (maxPrice && Number(maxPrice) >= 0)
            params.append("max_price", maxPrice);
        if (userId) params.append("user_id", userId);
        if (factionId) params.append("faction_id", factionId);
        return params.toString();
    }, [
        status,
        currency,
        offerType,
        search,
        minPrice,
        maxPrice,
        userId,
        factionId,
    ]);

    const { data, loading, error, refresh } = useApiGet<OfferType[]>(
        `/offers/list?${query}`,
        "Impossible de charger les offres",
    );

    // The same array while the data is unchanged: `data ?? []` alone gives a
    // new one on every render, which callers comparing it see as a change.
    const offers = useMemo(() => data ?? [], [data]);

    return { offers, loading, error, refresh };
}

export function useNewOffer(onCreated?: () => void): OfferFormHook {
    const { token } = useAuth();
    const { user, loading: userLoading, error: userError } = useMe();
    const { factions } = useFactions();
    const [audienceUsers, setAudienceUsers] = useState("");
    const [audienceFactions, setAudienceFactions] = useState("");
    const [expiresAt, setExpiresAt] = useState("");

    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState("");

    const [isOpen, setIsOpen] = useState<boolean>(false);
    const [forFaction, setForFaction] = useState(false);

    const form = useForm<OfferForm>({
        resolver: yupResolver(offerSchema),
    });

    const onSubmit = form.handleSubmit(async (data: OfferForm) => {
        setLoading(true);
        setMessage("");

        try {
            if (!token)
                throw new Error("You must be logged in to create an offer.");
            if (!user)
                throw new Error(
                    `Unable to get user information. ${userError ?? ""}`,
                );

            // Names are what people know: the API wants ids.
            const { userIds, factionIds } = await resolveAudience(
                audienceUsers,
                audienceFactions,
                factions,
            );

            const payload: OfferCreateData = {
                ...data,
                allowed_user_ids: userIds,
                allowed_faction_ids: factionIds,
                expires_at: fromLocalInput(expiresAt),
                user_id: forFaction ? null : user.user_id,
                faction_id: forFaction ? user.faction_id : null,
                init_quantity: data.quantity,
            };

            const res = await axios.post("/offers/create", payload);

            setMessage(
                `✅ Offer "${res.data.item_description}" created successfully`,
            );
            form.reset();
            setIsOpen(false);

            setForFaction(false);
            setAudienceUsers("");
            setAudienceFactions("");
            setExpiresAt("");
            onCreated?.();
        } catch (error: unknown) {
            if (axios.isAxiosError(error) && error.response?.status === 409) {
                setMessage("❌ Une offre identique existe déjà.");
            } else {
                setMessage(
                    `❌ Error creating offer: ${getErrorMessage(error)}`,
                );
            }
        } finally {
            setLoading(false);
        }
    });

    return {
        form,
        loading: loading || userLoading,
        message,
        onSubmit,
        isOpen,
        setIsOpen,
        forFaction,
        setForFaction,
        audienceUsers,
        setAudienceUsers,
        audienceFactions,
        setAudienceFactions,
        expiresAt,
        setExpiresAt,
    };
}
