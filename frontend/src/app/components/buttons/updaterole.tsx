import { useEffect, useId, useState } from "react";

import { useRoles } from "../hooks/factionroles";
import { useUpdateUser } from "../hooks/role";

interface UpdateRoleProps {
    userId: number;
    currentRoleId: number | null;
    factionId: number | null;
    onRoleUpdated?: () => void;
}

export function UpdateRole({
    userId,
    currentRoleId,
    factionId,
    onRoleUpdated,
}: UpdateRoleProps) {
    const {
        roles,
        loading: rolesLoading,
        error: rolesError,
    } = useRoles(factionId?.toString() ?? null);

    const { updateUser } = useUpdateUser();

    const [isOpen, setIsOpen] = useState(false);
    const [selectedRole, setSelectedRole] = useState<number | "">(
        currentRoleId ?? "",
    );
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState<string | null>(null);
    const titleId = useId();
    const fieldId = useId();

    const availableRoles =
        roles?.filter(
            (role) => role.name !== "Chef" && role.faction_id === factionId,
        ) ?? [];

    useEffect(() => {
        setSelectedRole(currentRoleId ?? "");
    }, [currentRoleId]);

    useEffect(() => {
        if (!isOpen) return;

        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === "Escape" && !loading) setIsOpen(false);
        };

        document.addEventListener("keydown", handleKeyDown);
        return () => document.removeEventListener("keydown", handleKeyDown);
    }, [isOpen, loading]);

    const openModal = () => {
        setSelectedRole(currentRoleId ?? "");
        setMessage(null);
        setIsOpen(true);
    };

    const closeModal = () => {
        if (!loading) setIsOpen(false);
    };

    const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
        e.preventDefault();
        if (selectedRole === "") {
            setMessage("Veuillez sélectionner un rôle.");
            return;
        }

        const roleExists = availableRoles.some(
            (role) => role.role_id === selectedRole,
        );
        if (!roleExists) {
            setMessage("Le rôle sélectionné n'est plus disponible.");
            return;
        }

        try {
            setLoading(true);
            setMessage(null);

            const res = await updateUser(userId, {
                role_id: selectedRole,
            });
            if (!res) {
                throw new Error("La mise à jour du rôle a échoué.");
            }

            setIsOpen(false);
            onRoleUpdated?.();
        } catch (error: unknown) {
            console.error("Échec de la mise à jour du rôle:", error);
            setMessage(
                error instanceof Error
                    ? error.message
                    : "Erreur inattendue lors de la mise à jour du rôle.",
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <button type="button" className="button" onClick={openModal}>
                edit
            </button>

            {isOpen && (
                <div className="modal-container" onClick={closeModal}>
                    <div
                        onClick={(e) => {
                            e.stopPropagation();
                        }}
                        className="modal"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby={titleId}
                    >
                        <h2 id={titleId}>Changer le rôle</h2>

                        {rolesLoading ? (
                            <p>Chargement des rôles...</p>
                        ) : rolesError ? (
                            <p role="alert">{rolesError}</p>
                        ) : (
                            <form onSubmit={handleSubmit}>
                                <div className="modal-field">
                                    <label htmlFor={fieldId}>
                                        Nouveau rôle
                                    </label>
                                    <select
                                        id={fieldId}
                                        value={selectedRole}
                                        disabled={loading}
                                        onChange={(e) =>
                                            setSelectedRole(
                                                e.target.value === ""
                                                    ? ""
                                                    : Number(e.target.value),
                                            )
                                        }
                                    >
                                        <option value="">
                                            Sélectionner un rôle
                                        </option>
                                        {availableRoles.map((role) => (
                                            <option
                                                key={role.role_id}
                                                value={role.role_id}
                                            >
                                                {role.name}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div className="modal-buttons">
                                    <button
                                        type="submit"
                                        disabled={loading}
                                        style={{
                                            flex: 1,
                                            backgroundColor: loading
                                                ? "#555"
                                                : "#4CAF50",
                                            padding: "10px 20px",
                                            border: "none",
                                            borderRadius: "6px",
                                            color: "white",
                                            cursor: loading
                                                ? "not-allowed"
                                                : "pointer",
                                        }}
                                    >
                                        {loading
                                            ? "Mise à jour..."
                                            : "Mettre à jour"}
                                    </button>
                                    <button
                                        type="button"
                                        onClick={closeModal}
                                        disabled={loading}
                                        style={{
                                            flex: 1,
                                            backgroundColor: "#d9534f",
                                            padding: "10px 20px",
                                            border: "none",
                                            borderRadius: "6px",
                                            color: "white",
                                            cursor: "pointer",
                                        }}
                                    >
                                        Annuler
                                    </button>
                                </div>

                                {message && (
                                    <p
                                        role="alert"
                                        style={{ marginTop: "10px" }}
                                    >
                                        {message}
                                    </p>
                                )}
                            </form>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
