import axios from "axios";
import { useCallback, useEffect, useState } from "react";

import { useApiGet } from "../../utils/useapiget";
import { getErrorMessage } from "../../utils/apierror";
import { applyTheme, storedTheme } from "../../utils/theme";
import type { PreferencesType } from "../../types/preferences";

/**
 * The account's preferences. The theme saved on the account is shown as soon
 * as it is known, so it follows the person from one browser to another.
 */
export function usePreferences() {
    const { data, loading, error, refresh } = useApiGet<PreferencesType>(
        "/preferences",
        "Erreur lors du chargement des préférences",
    );
    const [saving, setSaving] = useState(false);
    const [saveError, setSaveError] = useState("");

    useEffect(() => {
        if (data && data.theme !== storedTheme()) applyTheme(data.theme);
    }, [data]);

    const save = useCallback(
        async (changes: Partial<PreferencesType>) => {
            setSaving(true);
            setSaveError("");
            try {
                const res = await axios.put<PreferencesType>(
                    "/preferences",
                    changes,
                );
                applyTheme(res.data.theme);
                refresh();
                return true;
            } catch (err) {
                setSaveError(getErrorMessage(err));
                return false;
            } finally {
                setSaving(false);
            }
        },
        [refresh],
    );

    return {
        preferences: data,
        loading,
        error,
        saving,
        saveError,
        save,
    };
}
