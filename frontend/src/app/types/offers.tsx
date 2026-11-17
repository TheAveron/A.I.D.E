import type { HookForm, HookResult } from "./hooks";

export type OfferTypeLiteral = "BUY" | "SELL";
export type OfferStatusLiteral = "OPEN" | "CANCELLED" | "CLOSED";
export type OfferActionLitteral =
    "CREATED" | "UPDATED" | "DELETED" | "ACCEPTED" | "DECLINED";

export interface OfferBase {
    offer_type: OfferTypeLiteral;
    item_description: string;
    currency_name: string;
    price_per_unit: number;
    quantity: number;
    init_quantity: number;
}

export interface OfferCreateData extends OfferBase {
    // A private offer is addressed to these users and these factions' members
    allowed_user_ids: number[] | null;
    allowed_faction_ids: number[] | null;
    // The open offer is cancelled after this moment (ISO date); null: never
    expires_at?: string | null;
    user_id: number | null;
    faction_id: number | null;
}

export interface OfferType extends OfferCreateData {
    offer_id: number;
    is_private: boolean;
    expires_at: string | null;
    status: OfferStatusLiteral;
    created_at: string;
    updated_at: string;
}
export interface OfferCreate {
    offer_type: OfferTypeLiteral;
    item_description: string;
    currency_name: string;
    price_per_unit: number;
    quantity: number;
}

export interface OfferAcceptPayload {
    buyer_user_id?: number | null;
    buyer_faction_id?: number | null;
    quantity?: number;
}

export interface OfferResponse {
    offer_id: number;
    transaction_id: number;
    status: string;
}

export interface OfferHook extends HookResult {
    offer: OfferType | null;
}

export interface OffersHook extends HookResult {
    offers: OfferType[] | null;
    refresh: () => void;
}

export interface OfferFormHook extends HookForm<OfferCreate> {
    forFaction: boolean;
    setForFaction: React.Dispatch<React.SetStateAction<boolean>>;
    // Names separated by commas; empty means a public offer
    audienceUsers: string;
    setAudienceUsers: React.Dispatch<React.SetStateAction<string>>;
    audienceFactions: string;
    setAudienceFactions: React.Dispatch<React.SetStateAction<string>>;
    // Value of a datetime-local input; empty: the offer never expires
    expiresAt: string;
    setExpiresAt: React.Dispatch<React.SetStateAction<string>>;
}
