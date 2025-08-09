import { useState } from "react";

import { useRoles } from "../hooks/factionroles";
import { useUpdateUser } from "../hooks/role";

interface UpdateRoleProps {
    userId: number;
    currentRoleId: number | null;
    factionId: number | null;
    onRoleUpdated?: () => void; // optional callback
}

export function UpdateRole({
    userId,
    currentRoleId,
    factionId,
    onRoleUpdated,
}: UpdateRoleProps) {
    const { roles, loading: rolesLoading } = useRoles(
        factionId?.toString() ?? null
    );

    const { updateUser } = useUpdateUser();

    const [isOpen, setIsOpen] = useState(false);
    const [selectedRole, setSelectedRole] = useState<string>(
        currentRoleId?.toString() ?? ""
    );
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedRole) return;

        roles?.find((role) => role.name == selectedRole);

        try {
            setLoading(true);
            setMessage(null);

            const res = await updateUser(userId, { role_id: selectedRole });

            if (!res) {
                console.log(selectedRole);
            }

            setMessage("Rôle mis à jour avec succès.");
            if (onRoleUpdated) onRoleUpdated();
            setIsOpen(false);
        } catch (err: any) {
            setMessage("Erreur lors de la mise à jour du rôle.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <div className="button" onClick={() => setIsOpen(true)}>
                edit
            </div>

            {isOpen && (
                <div
                    className="modal-container"
                    onClick={() => setIsOpen(false)}
                >
                    <div
                        onClick={(e) => {
                            e.stopPropagation(); // stops bubbling to Link
                        }}
                        className="modal"
                    >
                        <h2>Changer le rôle</h2>

                        {rolesLoading ? (
                            <p>Chargement des rôles...</p>
                        ) : (
                            <form onSubmit={handleSubmit}>
                                <div className="modal-field">
                                    <label>Nouveau rôle</label>
                                    <select
                                        value={selectedRole}
                                        onChange={(e) =>
                                            setSelectedRole(e.target.value)
                                        }
                                    >
                                        <option value="">
                                            Sélectionner un rôle
                                        </option>
                                        {roles
                                            ?.filter(
                                                (r) =>
                                                    r.name !== "Chef" &&
                                                    r.faction_id === factionId
                                            )
                                            .map((role) => (
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
                                        onClick={() => setIsOpen(false)}
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
                                    <p style={{ marginTop: "10px" }}>
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
