export interface CurrencyType {
    name: string;
    symbol: string | null;
    faction_id: number;
    total_in_circulation: number;
    created_at: string;
    updated_at: string;
}
