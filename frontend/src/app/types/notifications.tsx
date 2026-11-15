export interface NotificationType {
    notification_id: number;
    kind: string;
    message: string;
    link: string | null;
    is_read: boolean;
    created_at: string;
}
