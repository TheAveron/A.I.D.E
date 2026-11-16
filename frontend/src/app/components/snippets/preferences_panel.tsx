import { usePreferences } from "../hooks/preferences";
import type { ThemePreference } from "../../types/preferences";

const THEMES: [ThemePreference, string][] = [
    ["dark", "Sombre"],
    ["light", "Clair"],
    ["system", "Comme l'appareil"],
];

/** Theme and notifications of the logged-in account. */
export default function PreferencesPanel() {
    const { preferences, loading, error, saving, saveError, save } =
        usePreferences();

    return (
        <div className="snippet-container">
            <h2>Préférences</h2>
            {error ? (
                <p role="alert">{error}</p>
            ) : loading || !preferences ? (
                <p>Chargement...</p>
            ) : (
                <>
                    <div className="modal-field">
                        <label htmlFor="theme-preference">Thème</label>
                        <select
                            id="theme-preference"
                            value={preferences.theme}
                            disabled={saving}
                            onChange={(e) =>
                                void save({
                                    theme: e.target.value as ThemePreference,
                                })
                            }
                        >
                            {THEMES.map(([value, label]) => (
                                <option key={value} value={value}>
                                    {label}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div className="modal-field">
                        <label>
                            <input
                                type="checkbox"
                                checked={preferences.notify_market}
                                disabled={saving}
                                onChange={(e) =>
                                    void save({
                                        notify_market: e.target.checked,
                                    })
                                }
                            />{" "}
                            Notifications du marché (offre acceptée, offre
                            expirée)
                        </label>
                    </div>
                    <div className="modal-field">
                        <label>
                            <input
                                type="checkbox"
                                checked={preferences.notify_faction}
                                disabled={saving}
                                onChange={(e) =>
                                    void save({
                                        notify_faction: e.target.checked,
                                    })
                                }
                            />{" "}
                            Notifications de faction (demandes d&apos;adhésion
                            et réponses, changement de rôle, direction)
                        </label>
                        <small>
                            Les avis de sécurité et de modération (mot de passe
                            réinitialisé, retrait d&apos;une faction, annulation
                            par un administrateur) arrivent toujours.
                        </small>
                    </div>
                </>
            )}
            {saveError && <p role="alert">{saveError}</p>}
        </div>
    );
}
