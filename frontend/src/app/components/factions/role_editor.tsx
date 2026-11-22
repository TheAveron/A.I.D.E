import axios from "axios";
import { useState, type FormEvent } from "react";

import { getErrorMessage } from "../../utils/apierror";
import {
    ROLE_PERMISSIONS,
    type RolePermission,
    type RoleType,
} from "../../types/roles";
import { isGuestRole } from "../../utils/roles";

type Draft = {
    name: string;
    description: string;
    permissions: Record<RolePermission, boolean>;
};

function draftOf(role: RoleType | null): Draft {
    return {
        name: role?.name ?? "",
        description: role?.description ?? "",
        permissions: Object.fromEntries(
            ROLE_PERMISSIONS.map(([key]) => [key, role?.[key] ?? false]),
        ) as Record<RolePermission, boolean>,
    };
}

/**
 * Create a role (`role` is null) or edit one. Nobody grants powers they don't
 * hold themselves (the server refuses it): those permissions are not offered,
 * unless the role already has them, shown then as they are.
 */
export default function RoleEditor({
    factionId,
    role,
    actorRole,
    onDone,
}: {
    factionId: number;
    role: RoleType | null;
    actorRole: RoleType;
    onDone: (changed: boolean) => void;
}) {
    const [draft, setDraft] = useState<Draft>(() => draftOf(role));
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    const submit = async (event: FormEvent) => {
        event.preventDefault();
        const name = draft.name.trim();
        if (!name || name.length > 50) {
            setError("Le nom doit faire entre 1 et 50 caractères");
            return;
        }
        const body = {
            name,
            description: draft.description.trim() || null,
            ...draft.permissions,
        };

        setSaving(true);
        setError("");
        try {
            if (role) {
                await axios.put(`/roles/update/${role.role_id}`, body);
            } else {
                await axios.post(`/roles/faction/${factionId}/create`, {
                    ...body,
                    faction_id: factionId,
                });
            }
            onDone(true);
        } catch (err) {
            setError(getErrorMessage(err));
            setSaving(false);
        }
    };

    return (
        <form className="snippet-container" onSubmit={submit}>
            <h3>{role ? `Modifier « ${role.name} »` : "Nouveau rôle"}</h3>
            <div className="modal-field">
                <label htmlFor="role-name">Nom</label>
                <input
                    id="role-name"
                    type="text"
                    maxLength={50}
                    // The guest role keeps its name: joining relies on it
                    readOnly={isGuestRole(role)}
                    value={draft.name}
                    onChange={(e) =>
                        setDraft({ ...draft, name: e.target.value })
                    }
                />
            </div>
            <div className="modal-field">
                <label htmlFor="role-description">Description</label>
                <input
                    id="role-description"
                    type="text"
                    value={draft.description}
                    onChange={(e) =>
                        setDraft({ ...draft, description: e.target.value })
                    }
                />
            </div>
            {ROLE_PERMISSIONS.map(([key, label]) => {
                const grantable = !!actorRole[key];
                if (!grantable && !role?.[key]) return null;
                return (
                    <label key={key} style={{ display: "block" }}>
                        <input
                            type="checkbox"
                            checked={draft.permissions[key]}
                            disabled={!grantable}
                            onChange={(e) =>
                                setDraft({
                                    ...draft,
                                    permissions: {
                                        ...draft.permissions,
                                        [key]: e.target.checked,
                                    },
                                })
                            }
                        />{" "}
                        {label}
                        {!grantable && (
                            <small> (vous ne pouvez pas le retirer)</small>
                        )}
                    </label>
                );
            })}
            <button type="submit" className="button" disabled={saving}>
                Enregistrer
            </button>{" "}
            <button
                type="button"
                className="button"
                disabled={saving}
                onClick={() => onDone(false)}
            >
                Annuler
            </button>
            {error && <p role="alert">{error}</p>}
        </form>
    );
}
