import type { ThemePreference } from "../types/preferences";

const STORAGE_KEY = "theme";

/** "system" follows the browser; otherwise the choice itself. */
export function resolveTheme(preference: ThemePreference): "dark" | "light" {
    if (preference === "system") {
        return window.matchMedia("(prefers-color-scheme: light)").matches
            ? "light"
            : "dark";
    }
    return preference;
}

export function storedTheme(): ThemePreference {
    try {
        const value = localStorage.getItem(STORAGE_KEY);
        if (value === "dark" || value === "light" || value === "system") {
            return value;
        }
    } catch {
        // Storage can be blocked: the default applies.
    }
    return "dark";
}

/** Show a theme now and remember it, so the next page load starts with it. */
export function applyTheme(preference: ThemePreference): void {
    document.documentElement.dataset.theme = resolveTheme(preference);
    try {
        localStorage.setItem(STORAGE_KEY, preference);
    } catch {
        // Not remembered, still applied.
    }
}

/**
 * Runs in <head> before the page is painted, so a light theme does not flash
 * dark first. Same rules as resolveTheme and storedTheme above.
 */
export const THEME_BOOT_SCRIPT = `try{var t=localStorage.getItem("${STORAGE_KEY}");var d=t==="light"||t==="dark"?t:t==="system"&&matchMedia("(prefers-color-scheme: light)").matches?"light":"dark";document.documentElement.dataset.theme=d}catch(e){}`;
