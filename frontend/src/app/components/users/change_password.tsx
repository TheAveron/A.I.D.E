import axios from "axios";
import { useState, type FormEvent } from "react";

import { useAuth } from "../../utils/authcontext";
import { applyAuthHeader } from "../../utils/authheader";
import { getErrorMessage } from "../../utils/apierror";
import type { AuthType } from "../../types/hooks";

// Same limits as the registration form.
const PASSWORD_MIN = 4;
const PASSWORD_MAX = 40;

/** Change the logged-in user's password; the session continues on a new token. */
export default function ChangePassword() {
    const { setToken } = useAuth();

    const [current, setCurrent] = useState("");
    const [next, setNext] = useState("");
    const [confirm, setConfirm] = useState("");
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState("");

    const validate = (): string => {
        if (!current) return "Le mot de passe actuel est obligatoire";
        if (next.length < PASSWORD_MIN)
            return `Le nouveau mot de passe doit faire au moins ${PASSWORD_MIN} caractères`;
        if (next.length > PASSWORD_MAX)
            return `Le nouveau mot de passe ne peut pas dépasser ${PASSWORD_MAX} caractères`;
        if (next !== confirm) return "Les mots de passe ne correspondent pas";
        return "";
    };

    const onSubmit = async (event: FormEvent) => {
        event.preventDefault();
        const problem = validate();
        if (problem) {
            setMessage(`❌ ${problem}`);
            return;
        }

        setLoading(true);
        setMessage("");
        try {
            const res = await axios.post<AuthType>("/auth/change-password", {
                current_password: current,
                new_password: next,
            });
            applyAuthHeader(res.data.access_token);
            setToken(res.data.access_token);
            setCurrent("");
            setNext("");
            setConfirm("");
            setMessage("✅ Mot de passe modifié");
        } catch (error: unknown) {
            if (axios.isAxiosError(error) && error.response?.status === 429) {
                setMessage(
                    "❌ Trop de tentatives échouées, réessayez dans quelques minutes",
                );
            } else {
                setMessage(`❌ ${getErrorMessage(error)}`);
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="snippet-container">
            <h2>Changer de mot de passe</h2>
            <form onSubmit={onSubmit}>
                <div className="modal-field">
                    <label htmlFor="current-password">
                        Mot de passe actuel
                    </label>
                    <input
                        id="current-password"
                        type="password"
                        autoComplete="current-password"
                        value={current}
                        onChange={(e) => setCurrent(e.target.value)}
                    />
                </div>
                <div className="modal-field">
                    <label htmlFor="new-password">Nouveau mot de passe</label>
                    <input
                        id="new-password"
                        type="password"
                        autoComplete="new-password"
                        value={next}
                        onChange={(e) => setNext(e.target.value)}
                    />
                </div>
                <div className="modal-field">
                    <label htmlFor="confirm-password">Confirmation</label>
                    <input
                        id="confirm-password"
                        type="password"
                        autoComplete="new-password"
                        value={confirm}
                        onChange={(e) => setConfirm(e.target.value)}
                    />
                </div>
                <button type="submit" className="button" disabled={loading}>
                    {loading ? "Modification..." : "Modifier"}
                </button>
            </form>
            {message && <p role="status">{message}</p>}
        </div>
    );
}
