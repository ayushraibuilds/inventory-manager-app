"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bell, X, Package, DollarSign, ShoppingCart, AlertTriangle, CheckCircle } from "lucide-react";
import { useAuth } from "@/components/AuthProvider";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Notification {
    id: string;
    action: string;
    item_name: string;
    details: string;
    created_at: string;
    read?: boolean;
}

const actionMeta: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
    ITEM_ADDED: { icon: <Package className="w-4 h-4" />, color: "text-emerald-400", label: "Product Added" },
    ITEM_UPDATED: { icon: <DollarSign className="w-4 h-4" />, color: "text-blue-400", label: "Price Updated" },
    ITEM_DELETED: { icon: <AlertTriangle className="w-4 h-4" />, color: "text-rose-400", label: "Product Removed" },
    BATCH_PRICE_UPDATE: { icon: <DollarSign className="w-4 h-4" />, color: "text-amber-400", label: "Batch Update" },
    ORDER_CREATED: { icon: <ShoppingCart className="w-4 h-4" />, color: "text-purple-400", label: "New Order" },
    CSV_IMPORT: { icon: <Package className="w-4 h-4" />, color: "text-cyan-400", label: "CSV Import" },
};

function timeAgo(dateStr: string) {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
}

export default function NotificationCenter() {
    const { sellerId, token } = useAuth();
    const [open, setOpen] = useState(false);
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [unreadCount, setUnreadCount] = useState(0);

    const fetchNotifications = useCallback(async () => {
        if (!sellerId || !token) return;
        try {
            const res = await fetch(
                `${API_URL}/api/activity?limit=20&seller_id=${encodeURIComponent(sellerId)}`,
                { headers: { Authorization: `Bearer ${token}` } }
            );
            if (!res.ok) return;
            const data = await res.json();
            const items = (data.logs || []).map((a: any, i: number) => ({
                id: a.id || String(i),
                action: a.action || "UNKNOWN",
                item_name: a.item_name || "",
                details: a.details || "",
                created_at: a.created_at || new Date().toISOString(),
            }));
            setNotifications(items);
            setUnreadCount(Math.min(items.length, 5));
        } catch { /* silent */ }
    }, [sellerId, token]);

    useEffect(() => {
        const initialFetch = window.setTimeout(() => {
            void fetchNotifications();
        }, 0);
        const interval = setInterval(fetchNotifications, 30000);
        return () => {
            clearTimeout(initialFetch);
            clearInterval(interval);
        };
    }, [fetchNotifications]);

    return (
        <>
            {/* Bell Button */}
            <button
                onClick={() => { setOpen(!open); setUnreadCount(0); }}
                className="relative flex items-center justify-center w-9 h-9 rounded-full bg-[var(--card-bg)] border border-[var(--border)] hover:bg-[var(--card-hover)] transition-all active:scale-90"
                title="Notifications"
            >
                <Bell className="w-4 h-4 text-[var(--text-muted)]" />
                {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 flex items-center justify-center w-4.5 h-4.5 min-w-[18px] rounded-full bg-rose-500 text-white text-[10px] font-bold">
                        {unreadCount}
                    </span>
                )}
            </button>

            {/* Panel */}
            <AnimatePresence>
                {open && (
                    <>
                        <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
                        <motion.div
                            initial={{ opacity: 0, y: -10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: -10, scale: 0.95 }}
                            className="fixed right-4 top-16 z-50 w-80 max-h-[70vh] bg-[var(--card-bg)] backdrop-blur-xl border border-[var(--border)] rounded-2xl shadow-2xl overflow-hidden"
                        >
                            <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)]">
                                <h3 className="text-sm font-bold text-[var(--text-primary)]">Notifications</h3>
                                <button onClick={() => setOpen(false)} className="text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                                    <X className="w-4 h-4" />
                                </button>
                            </div>
                            <div className="overflow-y-auto max-h-[60vh] divide-y divide-[var(--border)]">
                                {notifications.length === 0 ? (
                                    <div className="p-8 text-center text-sm text-[var(--text-muted)]">
                                        <CheckCircle className="w-8 h-8 mx-auto mb-2 opacity-30" />
                                        No notifications yet
                                    </div>
                                ) : (
                                    notifications.map((n) => {
                                        const meta = actionMeta[n.action] || { icon: <Bell className="w-4 h-4" />, color: "text-[var(--text-muted)]", label: n.action };
                                        return (
                                            <div key={n.id} className="px-4 py-3 hover:bg-[var(--card-hover)] transition-colors">
                                                <div className="flex items-start gap-3">
                                                    <div className={`mt-0.5 ${meta.color}`}>{meta.icon}</div>
                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-xs font-semibold text-[var(--text-primary)]">
                                                            {meta.label}
                                                            {n.item_name && <span className="font-normal text-[var(--text-muted)]"> — {n.item_name}</span>}
                                                        </p>
                                                        {n.details && (
                                                            <p className="text-xs text-[var(--text-muted)] mt-0.5 truncate">{n.details}</p>
                                                        )}
                                                        <p className="text-[10px] text-[var(--text-muted)] mt-1">{timeAgo(n.created_at)}</p>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })
                                )}
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </>
    );
}
