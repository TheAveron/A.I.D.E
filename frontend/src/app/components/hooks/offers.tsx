import { useState, useMemo } from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";

import * as yup from "yup";
import axios from "axios";

import { useAuth } from "../../utils/authcontext";
import { useApiGet } from "../../utils/useapiget";
import { useMe } from "./me";

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
        .oneOf(["BUY", "SELL"], "Offer type must be BUY or SELL")
        .required("Offer type is required"),
    item_description: yup
        .string()
        .required("Item description is required")
        .max(255, "Max 255 characters"),
    currency_name: yup.string().required("Currency name is required"),
    price_per_unit: yup
        .number()
        .typeError("Price must be a number")
        .positive("Price must be positive")
        .required("Price per unit is required"),
    quantity: yup
        .number()
        .typeError("Quantity must be a number")
        .integer("Quantity must be an integer")
        .positive("Quantity must be positive")
        .required("Quantity is required"),
});

export function useOffer(offer_id?: number): OfferHook {
    const { data, loading, error } = useApiGet<OfferType>(
        offer_id != null ? `/offers/detail/${offer_id}` : null,
        "Failed to fetch offer",
    );

    return { offer: data, loading, error };
}

// The server returns 50 offers unless asked for more (up to 200), newest first.
const MAX_OFFERS = "200";

export function useOffersList(
    currency?: string,
    status?: string,
    userId?: string | null,
    factionId?: string | null,
): OffersHook {
    const query = useMemo(() => {
        const params = new URLSearchParams({ limit: MAX_OFFERS });
        if (status) params.append("status", status);
        if (currency) params.append("currency", currency);
        // Filtered by the server: filtering the 200 newest offers here would hide the older offers of a user or of a faction.
        if (userId) params.append("user_id", userId);
        if (factionId) params.append("faction_id", factionId);
        return params.toString();
    }, [status, currency, userId, factionId]);

    const { data, loading, error, refresh } = useApiGet<OfferType[]>(
        `/offers/list?${query}`,
        "Failed to fetch offers",
    );

    return { offers: data ?? [], loading, error, refresh };
}

export function useNewOffer(onCreated?: () => void): OfferFormHook {
    const { token } = useAuth();
    const { user, loading: userLoading, error: userError } = useMe();

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

            const payload: OfferCreateData = {
                ...data,
                allowed_parties: null,
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
            onCreated?.();
        } catch (error: unknown) {
            if (axios.isAxiosError(error) && error.response?.status === 409) {
                setMessage("❌ Une offre identique existe déjà.");
            } else {
                setMessage(
                    `❌ Error creating offer: ${
                        axios.isAxiosError(error)
                            ? error.message
                            : "Unknown error"
                    }`,
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
    };
}
