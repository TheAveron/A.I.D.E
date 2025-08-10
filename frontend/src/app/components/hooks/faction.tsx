import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";

import axios from "axios";
import * as yup from "yup";

import { useAuth } from "../../utils/authprovider";
import { useMe } from "./me";

import type {
    FactionHook,
    FactionType,
    FactionFormData,
} from "../../types/factions";
import type { FactionFormHook } from "../../types/factions";

const factionSchema = yup.object().shape({
    name: yup.string().required("Le nom de la faction est obligatoire"),
    description: yup
        .string()
        .max(500, "La description est trop longue")
        .nullable()
        .default(null),

    is_approved: yup.boolean().default(false),
});

export function useFaction(faction_id: string | null): FactionHook {
    const { token } = useAuth();

    const [faction, setFaction] = useState<FactionType | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!token || !faction_id) return;

        const fetchFaction = async () => {
            try {
                setLoading(true);
                const res = await axios.get<FactionType>(
                    `/factions/detail/${faction_id}`
                );
                setFaction(res.data);
            } catch (error) {
                setError(`Error fetching faction: ${error}`);
            } finally {
                setLoading(false);
            }
        };

        fetchFaction();
    }, [token, faction_id]);

    return { faction, loading, error };
}

export function useNewFaction(): FactionFormHook {
    const { token } = useAuth();
    const { user, loading: userLoading, error: userError } = useMe();

    const [loading, setLoading] = useState<boolean>(false);
    const [message, setMessage] = useState<string>("");

    const [isOpen, setIsOpen] = useState<boolean>(false);

    const form = useForm<FactionFormData>({
        resolver: yupResolver(factionSchema),
    });

    const onSubmit = form.handleSubmit(async (data: FactionFormData) => {
        setLoading(true);
        setMessage("");

        try {
            if (!token) {
                throw new Error(
                    "Vous devez être connecté pour créer une faction."
                );
            }

            if (user?.faction_id) {
                throw new Error("Vous appartenez déjà à une faction.");
            }

            if (userError) {
                throw new Error(userError);
            }

            const payload = {
                ...data,
                is_approved: false,
            };

            const res = await axios.post<FactionType>(
                "/factions/create",
                payload
            );

            setMessage(`✅ Faction "${res.data.name}" créée avec succès`);
            form.reset();
            setIsOpen(false);

            window.location.reload();
        } catch (error: any) {
            if (error.response?.status === 409) {
                setMessage("❌ Une faction avec ce nom existe déjà.");
            } else {
                setMessage("❌ Erreur lors de la création de la faction.");
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
