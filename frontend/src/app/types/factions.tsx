export interface FactionFormData {
    name: string;
    description: string | null;
    is_approved: boolean;
}

export interface FactionType extends FactionFormData {
    faction_id: number;
    created_at: string;
}
