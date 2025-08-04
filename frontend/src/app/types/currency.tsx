export interface CurrencyFormData {
    name: string;
    symbol: string | null;
    total_in_circulation: number;
}

export interface CurrencyType extends CurrencyFormData {
    faction_id: number;
    created_at: string;
    updated_at: string;
}
