export interface Notification {
    id: string;
    type: string;
    message: string;
    is_read: boolean;
    created_at: string;
    user_id: string;
}

export interface NotificationStreamEvent {
    event_type: "notification" | "unread_count" | "connected";
    id?: string;
    type?: string;
    message?: string;
    is_read?: boolean;
    created_at?: string;
    user_id?: string;
    // For unread_count events
    unread_count?: number;
    // For connected events
    status?: string;
}

export const NotificationType = {
    TICKET_UPLOADED: "ticket_uploaded",
    PAYMENT_SUCCESS: "payment_success",
    PAYMENT_FAILED: "payment_failed",
    BOOKING_CONFIRMED: "booking_confirmed",
    GENERAL: "general",
} as const;

export type NotificationTypeValue = typeof NotificationType[keyof typeof NotificationType];
