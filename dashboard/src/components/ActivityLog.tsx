"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Clock, Plus, Pencil, Trash2, MessageSquare, AlertCircle } from "lucide-react";
import { toast } from "sonner";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ActivityEntry {
    id: number;
    timestamp: string;
    seller_id: string;
    action: string;
    item_name: string;
    details: string;
}

const ACTION_ICONS: Record<string, React.ReactNode> = {
    ITEM_ADDED: <Plus className="w-3.5 h-3.5 text-green-400" />,
    ITEM_UPDATED: <Pencil className="w-3.5 h-3.5 text-blue-400" />,
    ITEM_DELETED: <Trash2 className="w-3.5 h-3.5 text-red-400" />,
    BULK_DELETE: <Trash2 className="w-3.5 h-3.5 text-red-400" />,
    ADD_VIA_WHATSAPP: <MessageSquare className="w-3.5 h-3.5 text-green-400" />,
    UPDATE_VIA_WHATSAPP: <MessageSquare className="w-3.5 h-3.5 text-blue-400" />,
    DELETE_VIA_WHATSAPP: <MessageSquare className="w-3.5 h-3.5 text-red-400" />,
    UNKNOWN_INTENT: <AlertCircle className="w-3.5 h-3.5 text-yellow-400" />,
};

const ACTION_LABELS: Record<string, string> = {
    ITEM_ADDED: "Added",
    ITEM_UPDATED: "Updated",
    ITEM_DELETED: "Deleted",
    BULK_DELETE: "Bulk Delete",
    ADD_VIA_WHATSAPP: "WhatsApp Add",
    UPDATE_VIA_WHATSAPP: "WhatsApp Update",
    DELETE_VIA_WHATSAPP: "WhatsApp Delete",
    UNKNOWN_INTENT: "Unknown",
};

function timeAgo(timestamp: string): string {
    const diff = Date.now() - new Date(timestamp + "Z").getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
}

interface ActivityLogProps {
    selectedSeller: string;
}

export default function ActivityLog({ selectedSeller }: ActivityLogProps) {
    const [logs, setLogs] = useState<ActivityEntry[]>([]);

    const fetchLogs = useCallback(async () => {
        try {
            const sellerParam = selectedSeller !== "all" ? `&seller_id=${encodeURIComponent(selectedSeller)}` : "";
            const res = await fetch(`${API_URL}/api/activity?limit=20${sellerParam}`);

            if (res.status === 429) {
                // Silently skip to avoid spamming since it's a 5s bg poll
                return;
            }
            if (res.ok) {
                const data = await res.json();
                setLogs(data.logs || []);
            }
        } catch {
            // silently fail
        }
    }, [selectedSeller]);

    useEffect(() => {
        fetchLogs();
        const interval = setInterval(fetchLogs, 5000);
        return () => clearInterval(interval);
    }, [fetchLogs]);

    return (
        <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-[var(--card-bg)] backdrop-blur-xl border border-[var(--border)] rounded-2xl p-6 shadow-2xl"
        >
            <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                <Clock className="w-5 h-5 text-primary" />
                Activity Log
            </h2>

            {logs.length === 0 ? (
                <div className="text-center py-8 text-[var(--text-muted)] text-sm">
                    <Clock className="w-6 h-6 mx-auto mb-2 opacity-40" />
                    No activity yet
                </div>
            ) : (
                <div className="space-y-1 max-h-80 overflow-y-auto pr-1 scrollbar-thin">
                    <AnimatePresence mode="popLayout">
                        {logs.map((log) => (
                            <motion.div
                                key={log.id}
                                initial={{ opacity: 0, x: 10 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0 }}
                                className="flex items-start gap-3 py-2.5 px-3 rounded-lg hover:bg-[var(--card-hover)] transition-colors group"
                            >
                                <div className="mt-0.5 w-7 h-7 rounded-full bg-[var(--card-hover)] border border-[var(--border)] flex items-center justify-center flex-shrink-0">
                                    {ACTION_ICONS[log.action] || <Clock className="w-3.5 h-3.5 text-[var(--text-muted)]" />}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs font-semibold text-[var(--text-primary)]">
                                            {ACTION_LABELS[log.action] || log.action}
                                        </span>
                                        <span className="text-xs text-[var(--text-muted)]">{timeAgo(log.timestamp)}</span>
                                    </div>
                                    <p className="text-xs text-[var(--text-secondary)] truncate mt-0.5">
                                        {log.item_name || log.details || "—"}
                                    </p>
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            )}
        </motion.div>
    );
}
