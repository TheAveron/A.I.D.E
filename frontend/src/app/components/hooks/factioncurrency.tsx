import { useState } from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";

import * as yup from "yup";
import axios from "axios";

import { useAuth } from "../../utils/authcontext";
import { getErrorMessage } from "../../utils/apierror";
import { useApiGet } from "../../utils/useapiget";
import { useMe } from "../hooks/me";

import type {
    CurrencyHook,
    CurrencyType,
    CurrencyForm,
    CurrencyFormHook,
    CurrencyCreateData,
} from "../../types/currency";

const currencySchema = yup.object().shape({
    name: yup.string().required("Le nom de la monnaie est obligatoire"),
    symbol: yup.string().optional().nullable().default(null),
    total_in_circulation: yup
        .number()
        .typeError("Doit être un nombre")
        .min(0, "La quantité ne peut pas être négative")
        .required("La quantité en circulation est obligatoire"),
});

export function useCurrency(faction_id: string | null): CurrencyHook {
    // The server answers `null` (not an error) for a faction without currency.
    const { data, loading, error, refresh } = useApiGet<CurrencyType | null>(
        faction_id
            ? `/currencies/faction/${encodeURIComponent(faction_id)}`
            : null,
        "❌ Error fetching currency",
    );

    return { currency: data, loading, error, refresh };
}

export function useNewCurrency(onCreated?: () => void): CurrencyFormHook {
    const { token } = useAuth() ?? {};

    const { user, loading: userLoading, error: userError } = useMe();

    const [loading, setLoading] = useState<boolean>(false);
    const [message, setMessage] = useState<string>("");

    const [isOpen, setIsOpen] = useState<boolean>(false);

    const form = useForm<CurrencyForm>({
        resolver: yupResolver(currencySchema),
    });

    const onSubmit = form.handleSubmit(async (data: CurrencyForm) => {
        setLoading(true);
        setMessage("");

        try {
            if (!token) {
                throw new Error(
                    "Vous devez être connecté pour créer une monnaie.",
                );
            }
            if (!user)
                throw new Error(
                    `Unable to get user information. ${userError ?? ""}`,
                );

            const payload: CurrencyCreateData = {
                ...data,
                faction_id: user?.faction_id,
            };

            const res = await axios.post<CurrencyType>(
                "/currencies/create",
                payload,
            );

            setMessage(`✅ Monnaie "${res.data.name}" créée avec succès`);
            form.reset();
            setIsOpen(false);
            onCreated?.();
        } catch (error: unknown) {
            if (axios.isAxiosError(error) && error.response?.status === 409) {
                setMessage(
                    "❌ Une monnaie avec ce nom ou symbole existe déjà.",
                );
            } else {
                setMessage(
                    `❌ Erreur lors de la création de la monnaie : ${getErrorMessage(error)}`,
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
    };
}
