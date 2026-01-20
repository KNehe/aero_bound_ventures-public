"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import useAuth from "@/store/auth";
import { Notification } from "@/types/notifications";
import { apiClient, getApiBaseUrl } from "@/lib/api";

const API_BASE_URL = getApiBaseUrl();

interface CursorPaginatedNotificationResponse {
    items: Notification[];
    next_cursor: string | null;
    has_more: boolean;
    has_previous: boolean;
    total_count: number | null;
    limit: number;
}

interface UseNotificationsReturn {
    notifications: Notification[];
    unreadCount: number;
    isConnected: boolean;
    isLoading: boolean;
    error: string | null;
    markAsRead: (notificationId: string) => Promise<void>;
    markAllAsRead: () => Promise<void>;
    deleteNotification: (notificationId: string) => Promise<void>;
    refetch: () => Promise<void>;
}

export function useNotifications(): UseNotificationsReturn {
    const { isAuthenticated } = useAuth();
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [isConnected, setIsConnected] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const eventSourceRef = useRef<EventSource | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const reconnectAttempts = useRef(0);
    const maxReconnectAttempts = 5;

    const fetchNotifications = useCallback(async () => {
        if (!isAuthenticated) return;

        setIsLoading(true);
        try {
            const data = await apiClient.get<CursorPaginatedNotificationResponse>('/notifications/?limit=20&include_count=true');
            setNotifications(data.items);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to fetch notifications");
        } finally {
            setIsLoading(false);
        }
    }, [isAuthenticated]);

    const connectSSE = useCallback(() => {
        if (!isAuthenticated) return;

        if (eventSourceRef.current) {
            eventSourceRef.current.close();
        }

        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }

        const sseUrl = `${API_BASE_URL}/notifications/stream`;
        const eventSource = new EventSource(sseUrl, { withCredentials: true });
        eventSourceRef.current = eventSource;

        eventSource.onopen = () => {
            setIsConnected(true);
            setError(null);
            reconnectAttempts.current = 0;
            console.log("SSE connection established");
        };

        // Handle connected event (initial)
        eventSource.addEventListener("connected", (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.unread_count !== undefined) {
                    setUnreadCount(data.unread_count);
                }
                console.log("SSE connected event received:", data);
            } catch (err) {
                console.error("Failed to parse connected event:", err);
            }
        });

        // Handle notification events
        eventSource.addEventListener("notification", (event) => {
            try {
                const notification = JSON.parse(event.data);
                console.log("New notification received:", notification);
                // Add to beginning of list
                setNotifications((prev) => [notification, ...prev]);
                if (!notification.is_read) {
                    setUnreadCount((prev) => prev + 1);
                }
            } catch (err) {
                console.error("Failed to parse notification event:", err);
            }
        });

        // Handle unread_count events
        eventSource.addEventListener("unread_count", (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.unread_count !== undefined) {
                    setUnreadCount(data.unread_count);
                }
            } catch (err) {
                console.error("Failed to parse unread_count event:", err);
            }
        });

        // Handle errors
        eventSource.onerror = (event) => {
            console.error("SSE error:", event);
            setIsConnected(false);

            // Close current connection
            eventSource.close();
            eventSourceRef.current = null;

            // Attempt reconnect with exponential backoff
            if (reconnectAttempts.current < maxReconnectAttempts) {
                const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
                reconnectAttempts.current += 1;
                console.log(`SSE reconnecting in ${delay}ms (attempt ${reconnectAttempts.current})`);

                reconnectTimeoutRef.current = setTimeout(() => {
                    if (isAuthenticated) {
                        connectSSE();
                    }
                }, delay);
            } else {
                setError("Connection lost. Please refresh the page.");
            }
        };

        return () => {
            eventSource.close();
        };
    }, [isAuthenticated]);

    // Setup SSE connection when authenticated
    useEffect(() => {
        if (isAuthenticated) {
            fetchNotifications();
            const cleanup = connectSSE();
            return cleanup;
        } else {
            // Clear state when logged out
            setNotifications([]);
            setUnreadCount(0);
            setIsConnected(false);
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
                eventSourceRef.current = null;
            }
        }
    }, [isAuthenticated, fetchNotifications, connectSSE]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
        };
    }, []);

    // Mark single notification as read
    const markAsRead = useCallback(
        async (notificationId: string) => {
            if (!isAuthenticated) return;

            const notification = notifications.find((n) => n.id === notificationId);
            if (notification?.is_read) return;

            try {
                await apiClient.put(`/notifications/${notificationId}/mark-read`);
                setNotifications((prev) =>
                    prev.map((n) => (n.id === notificationId ? { ...n, is_read: true } : n))
                );
                setUnreadCount((prev) => Math.max(0, prev - 1));
            } catch (err) {
                console.error("Failed to mark notification as read:", err);
            }
        },
        [isAuthenticated, notifications]
    );

    // Mark all notifications as read
    const markAllAsRead = useCallback(async () => {
        if (!isAuthenticated) return;

        try {
            await apiClient.put('/notifications/mark-all-read');
            setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
            setUnreadCount(0);
        } catch (err) {
            console.error("Failed to mark all notifications as read:", err);
        }
    }, [isAuthenticated]);

    // Delete notification
    const deleteNotification = useCallback(
        async (notificationId: string) => {
            if (!isAuthenticated) return;

            try {
                await apiClient.delete(`/notifications/${notificationId}`);
                const deletedNotification = notifications.find((n) => n.id === notificationId);
                setNotifications((prev) => prev.filter((n) => n.id !== notificationId));
                if (deletedNotification && !deletedNotification.is_read) {
                    setUnreadCount((prev) => Math.max(0, prev - 1));
                }
            } catch (err) {
                console.error("Failed to delete notification:", err);
            }
        },
        [isAuthenticated, notifications]
    );

    return {
        notifications,
        unreadCount,
        isConnected,
        isLoading,
        error,
        markAsRead,
        markAllAsRead,
        deleteNotification,
        refetch: fetchNotifications,
    };
}
