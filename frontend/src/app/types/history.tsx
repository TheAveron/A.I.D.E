import type { HookResult } from "./hooks";
import type { OfferActionLitteral } from "./offers";

export interface OfferHistoryType {
    offer_id: number;
    actor_user_id: number | null;
    actor_faction_id: number | null;
    action: OfferActionLitteral;
    notes: string | null;
    history_id: number;
    timestamp: string;
}

export interface OfferHistoryHook extends HookResult {
    offerHistory: OfferHistoryType | null;
}

export interface OfferHistoriesHook extends HookResult {
    offerHistories: OfferHistoryType[] | null;
}
