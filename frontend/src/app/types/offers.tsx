export interface OfferInfo {
    offer_type: "BUY" | "SELL";
    item_description: string[];
    currency: string;
    price_per_unit: number;
    quantity: number;
    allowed_parties: number[];
    offer_id: number;
    user_id: number | null;
    faction_id: number | null;
    status: "OPEN" | "CANCELLED" | "CLOSED";
    created_at: string;
}
