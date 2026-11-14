import { useState, useMemo } from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";

import * as yup from "yup";
import axios from "axios";

import { useAuth } from "../../utils/authcontext";
import { getErrorMessage } from "../../utils/apierror";
import { useApiGet } from "../../utils/useapiget";
import { useMe } from "./me";
import { useFactions } from "./factions";

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

        .max(1e12, "Price is too high")
        .required("Price per unit is required"),
    quantity: yup
        .number()
        .typeError("Quantity must be a number")
        .integer("Quantity must be an integer")
        .positive("Quantity must be positive")
        .max(2147483647, "Quantity is too high")
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

/** The comma-separated names typed in a form, trimmed, without blanks. */
function splitNames(text: string): string[] {
    return text
        .split(",")
        .map((name) => name.trim())
        .filter(Boolean);
}

export function useNewOffer(onCreated?: () => void): OfferFormHook {
    const { token } = useAuth();
    const { user, loading: userLoading, error: userError } = useMe();
    const { factions } = useFactions();
    const [audienceUsers, setAudienceUsers] = useState("");
    const [audienceFactions, setAudienceFactions] = useState("");

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

            const userNames = splitNames(audienceUsers);
            const factionNames = splitNames(audienceFactions);

            // Names are what people know: the API wants ids.
            const allowedUserIds: number[] = [];
            for (const name of userNames) {
                try {
                    const res = await axios.get<{ user_id: number }>(
                        `/users/from_name/${encodeURIComponent(name)}`,
                    );
                    allowedUserIds.push(res.data.user_id);
                } catch (error: unknown) {
                    if (
                        axios.isAxiosError(error) &&
                        error.response?.status === 404
                    ) {
                        throw new Error(`Utilisateur inconnu : ${name}`);
                    }
                    throw error;
                }
            }
            const allowedFactionIds = factionNames.map((name) => {
                const found = factions?.find(
                    (f) => f.name.toLowerCase() === name.toLowerCase(),
                );
                if (!found) throw new Error(`Faction inconnue : ${name}`);
                return found.faction_id;
            });

            const payload: OfferCreateData = {
                ...data,
                allowed_user_ids: allowedUserIds.length ? allowedUserIds : null,
                allowed_faction_ids: allowedFactionIds.length
                    ? allowedFactionIds
                    : null,
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
    };
}
