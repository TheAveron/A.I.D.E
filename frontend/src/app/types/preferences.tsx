export type ThemePreference = "dark" | "light" | "system";

/** What the map shows (only what is hidden: anything new shows). */
export interface MapDisplay {
    hidden_layers: ("territories" | "stations" | "markers" | "players")[];
    hidden_kinds: string[];
    /** Faction ids; null for the players' own territories. */
    hidden_factions: (number | null)[];
}

export interface PreferencesType {
    theme: ThemePreference;
    // Notifications about offers (accepted, expired)
    notify_market: boolean;
    // Notifications about factions (join requests and answers, roles, leadership)
    notify_faction: boolean;
    map_display: MapDisplay | null;
}
