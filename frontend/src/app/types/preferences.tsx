export type ThemePreference = "dark" | "light" | "system";

export interface PreferencesType {
    theme: ThemePreference;
    // Notifications about offers (accepted, expired)
    notify_market: boolean;
    // Notifications about factions (join requests and answers, roles, leadership)
    notify_faction: boolean;
}
