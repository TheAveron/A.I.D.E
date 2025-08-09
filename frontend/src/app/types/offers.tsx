import type { UseFormReturn } from "react-hook-form";
import type { HookForm, HookResult } from "./hooks";

export type OfferTypeLiteral = "BUY" | "SELL";
export type OfferStatusLiteral = "OPEN" | "CANCELLED" | "CLOSED";
export type OfferActionLitteral =
    | "CREATED"
    | "UPDATED"
    | "DELETED"
    | "ACCEPTED"
    | "DECLINED";

export interface OfferBase {
    offer_type: OfferTypeLiteral;
    item_description: string;
    currency_name: string;
    price_per_unit: number;
    quantity: number;
    init_quantity: number;
}

export interface OfferCreateData extends OfferBase {
    allowed_parties: string | null;
    user_id: number | null;
    faction_id: number | null;
}

export interface OfferType extends OfferCreateData {
    offer_id: number;
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
    offer_id: 0;
    transaction_id: 0;
    status: "string";
}

export interface OfferHook extends HookResult {
    offer: OfferType | null;
}

export interface OffersHook extends HookResult {
    offers: OfferType[] | null;
}

export interface OfferFormHook extends HookForm {
    form: UseFormReturn<OfferCreate, any, OfferCreate>;
    forFaction: boolean;
    setForFaction: React.Dispatch<React.SetStateAction<boolean>>;
}
