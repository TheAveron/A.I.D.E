export type TrainService = "O" | "E" | "F" | "L";

export interface TrainType {
    train_id: number;
    // "A-E07 Aurore": built by the server, never typed
    display_name: string;
    line: string;
    service: TrainService | null;
    number: number;
    common_name: string | null;
    // The name under the old convention ("MMP1-1")
    legacy_id: string | null;
    owner_user_id: number | null;
    owner_faction_id: number | null;
    owner_name: string | null;
    created_by_user_id: number | null;
    created_at: string;
    updated_at: string;
    retired_at: string | null;
}

export interface TrainHistoryType {
    history_id: number;
    action: "CREATED" | "UPDATED" | "RETIRED";
    old_name: string | null;
    new_name: string | null;
    actor_user_id: number | null;
    created_at: string;
}

export interface LineStationType {
    station_id: number;
    name: string;
    x: number;
    y: number | null;
    z: number;
    dimension: "overworld" | "nether" | "end";
}

export interface LineType {
    line_id: number;
    code: string;
    name: string | null;
    color: string | null;
    description: string | null;
    owner_faction_id: number | null;
    stops: { position: number; station: LineStationType }[];
}

export interface TrainFilters {
    line?: string;
    service?: string;
    q?: string;
    includeRetired?: boolean;
    ownerUserId?: number | null;
    ownerFactionId?: number | null;
}

export interface PlatformType {
    platform_id: number;
    name: string;
    description: string | null;
}

export interface StationType extends LineStationType {
    description: string | null;
    created_by_user_id: number | null;
    created_at: string;
    updated_at: string;
    platforms: PlatformType[];
}

export const DIMENSIONS = {
    overworld: "Overworld",
    nether: "Nether",
    end: "End",
} as const;
