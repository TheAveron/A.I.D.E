import { useEffect, useState, useMemo } from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";

import * as yup from "yup";
import axios from "axios";

import { useAuth } from "../../utils/authprovider";
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
    const { token } = useAuth();

    const [offer, setOffer] = useState<OfferType | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!token) return;

        const fetchOffer = async () => {
            setLoading(true);
            setError(null);

            try {
                const res = await axios.get<OfferType>(
                    `/offers/detail/${offer_id}`
                );

                setOffer(res.data);
            } catch (err: any) {
                setError(err.message || "Failed to fetch offer");
            } finally {
                setLoading(false);
            }
        };

        fetchOffer();
    }, [token, offer_id]);

    return { offer, loading, error };
}

export function useOffersList(currency?: string, status?: string): OffersHook {
    const { token } = useAuth();

    const [offers, setOffers] = useState<OfferType[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const query = useMemo(() => {
        const params = new URLSearchParams();
        if (status) params.append("status", status);
        if (currency) params.append("currency", currency);
        return params.toString();
    }, [status, currency]);

    useEffect(() => {
        if (!token) return;

        const fetchOffers = async () => {
            setLoading(true);
            setError(null);

            try {
                const res = await axios.get<OfferType[]>(
                    `/offers/list?${query}`
                );
                setOffers(res.data);
            } catch (err: any) {
                console.error("Error fetching offers:", err);
                setError(err.message || "Failed to fetch offers");
            } finally {
                setLoading(false);
            }
        };

        fetchOffers();
    }, [token, query]);

    return { offers, loading, error };
}

export function useNewOffer(): OfferFormHook {
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
                    `Unable to get user information. ${userError ?? ""}`
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
                `✅ Offer "${res.data.item_description}" created successfully`
            );
            form.reset();
            setIsOpen(false);

            setForFaction(false);
            window.location.reload();
        } catch (error: any) {
            if (error.response?.status === 409) {
                setMessage("❌ Une offre identique existe déjà.");
            } else {
                setMessage(`❌ Error creating offer: ${error.message}`);
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
