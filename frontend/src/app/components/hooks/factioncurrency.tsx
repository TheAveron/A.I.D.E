import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";

import * as yup from "yup";
import axios from "axios";

import { useAuth } from "../../utils/authprovider";
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
    const { token } = useAuth();

    const [currency, setCurrency] = useState<CurrencyType | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!token) {
            throw new Error("Vous devez être connecté pour créer une faction.");
        }

        if (!faction_id) {
            throw new Error("Aucune faction n'a été renseignée");
        }

        const fetchCurrency = async () => {
            try {
                setLoading(true);
                const res = await axios.get<CurrencyType>(
                    `http://127.0.0.1:8000/currencies/faction/${faction_id}`,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );
                setCurrency(res.data);
            } catch (error) {
                setError(`❌ Error fetching currency: ${error}`);
            } finally {
                setLoading(false);
            }
        };

        fetchCurrency();
    }, [token, faction_id]);

    return { currency, loading, error };
}

export function useNewCurrency(): CurrencyFormHook {
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
                    "Vous devez être connecté pour créer une monnaie."
                );
            }
            if (!user)
                throw new Error(
                    `Unable to get user information. ${userError ?? ""}`
                );

            const payload: CurrencyCreateData = {
                ...data,
                faction_id: user?.faction_id,
            };

            const res = await axios.post<CurrencyType>(
                "http://localhost:8000/currencies/create",
                payload
            );

            setMessage(`✅ Monnaie "${res.data.name}" créée avec succès`);
            form.reset();
            setIsOpen(false);
            window.location.reload();
        } catch (error: any) {
            if (error.response?.status === 409) {
                setMessage(
                    "❌ Une monnaie avec ce nom ou symbole existe déjà."
                );
            } else {
                setMessage("❌ Erreur lors de la création de la monnaie.");
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
