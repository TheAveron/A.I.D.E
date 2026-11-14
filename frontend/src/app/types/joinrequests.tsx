export interface JoinRequestType {
    request_id: number;
    user_id: number;
    username: string;
    faction_id: number;
    status: "PENDING" | "ACCEPTED" | "REFUSED" | "CANCELLED";
    message: string | null;
    created_at: string;
    decided_at: string | null;
}
