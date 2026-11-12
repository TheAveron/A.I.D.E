import { useState } from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";

import axios from "axios";
import * as yup from "yup";

import { useAuth } from "../../utils/authcontext";
import { getErrorMessage } from "../../utils/apierror";
import { useApiGet } from "../../utils/useapiget";
import { useMe } from "./me";

import type {
    FactionHook,
    FactionType,
    FactionFormData,
} from "../../types/factions";
import type { FactionFormHook } from "../../types/factions";
import { useUpdateUser } from "./role";

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
    const { data, loading, error } = useApiGet<FactionType>(
        faction_id
            ? `/factions/detail/${encodeURIComponent(faction_id)}`
            : null,
        "Error fetching faction",
    );

    return { faction: data, loading, error };
}

export function useNewFaction(onCreated?: () => void): FactionFormHook {
    const { token } = useAuth();
    const { user, loading: userLoading, error: userError } = useMe();
    const { faction: UserFaction } = useFaction(
        user?.faction_id?.toString() || null,
    );

    const { updateUser } = useUpdateUser();

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
                    "Vous devez être connecté pour créer une faction.",
                );
            }

            if (UserFaction && UserFaction.name != "Sans Faction") {
                throw new Error("Vous appartenez déjà à une faction.");
            } else if (UserFaction && UserFaction.name == "Sans Faction") {
                updateUser(user?.user_id || null, { faction_id: null });
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
                payload,
            );

            setMessage(`✅ Faction "${res.data.name}" créée avec succès`);
            form.reset();
            setIsOpen(false);

            onCreated?.();
        } catch (error: unknown) {
            if (axios.isAxiosError(error) && error.response?.status === 409) {
                setMessage("❌ Une faction avec ce nom existe déjà.");
            } else {
                setMessage(
                    `❌ Erreur lors de la création de la faction : ${getErrorMessage(error)}`,
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
