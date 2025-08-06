import type { UseFormReturn } from "react-hook-form";
import type { HookForm, HookResult } from "./hooks";

export type OfferTypeLiteral = "BUY" | "SELL";
export type OfferStatusLiteral = "OPEN" | "CANCELLED" | "CLOSED";

export interface OfferBase {
    offer_type: OfferTypeLiteral;
    item_description: string;
    currency_name: string;
    price_per_unit: number;
    quantity: number;
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

export interface OfferHook extends HookResult {
    offer: OfferType | null;
}

export interface OffersHook extends HookResult {
    offers: OfferType[] | null;
}

export interface OfferFormHook extends HookForm {
    form: UseFormReturn<OfferBase, any, OfferBase>;
    forFaction: boolean;
    setForFaction: React.Dispatch<React.SetStateAction<boolean>>;
}
