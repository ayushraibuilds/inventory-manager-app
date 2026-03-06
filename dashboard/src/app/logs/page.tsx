"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    ArrowLeft,
    MessageSquare,
    Mic,
    Image as ImageIcon,
    Clock,
    User,
    RefreshCcw,
    Search,
} from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/components/AuthProvider";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface LogEntry {
    id: string;
    action: string;
    item_name: string;
    details: string;
    created_at: string;
}

function timeAgo(dateStr: string) {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
}

function actionIcon(action: string) {
    if (action.includes("VOICE") || action.includes("AUDIO")) return <Mic className="w-4 h-4 text-purple-400" />;
    if (action.includes("IMAGE")) return <ImageIcon className="w-4 h-4 text-cyan-400" />;
    return <MessageSquare className="w-4 h-4 text-blue-400" />;
}

function actionBadge(action: string) {
    const colors: Record<string, string> = {
        ITEM_ADDED: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        ITEM_UPDATED: "bg-blue-500/10 text-blue-400 border-blue-500/20",
        ITEM_DELETED: "bg-rose-500/10 text-rose-400 border-rose-500/20",
        BATCH_PRICE_UPDATE: "bg-amber-500/10 text-amber-400 border-amber-500/20",
        CSV_IMPORT: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
        WHATSAPP_MESSAGE: "bg-green-500/10 text-green-400 border-green-500/20",
    };
    const c = colors[action] || "bg-[var(--card-bg)] text-[var(--text-muted)] border-[var(--border)]";
    return (
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${c}`}>
            {action.replace(/_/g, " ")}
        </span>
    );
}

export default function WebhookLogsPage() {
    const { sellerId, token, isLoading: authLoading } = useAuth();
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");

    const fetchLogs = useCallback(async () => {
        if (!sellerId || !token) return;
        try {
            const res = await fetch(
                `${API_URL}/api/activity?limit=50&seller_id=${encodeURIComponent(sellerId)}`,
                { headers: { Authorization: `Bearer ${token}` } }
            );
            if (!res.ok) return;
            const data = await res.json();
            setLogs(
                (data.logs || []).map((a: any, i: number) => ({
                    id: a.id || String(i),
                    action: a.action || "UNKNOWN",
                    item_name: a.item_name || "",
                    details: a.details || "",
                    created_at: a.created_at || new Date().toISOString(),
                }))
            );
        } catch { /* silent */ }
        finally { setLoading(false); }
    }, [sellerId, token]);

    useEffect(() => {
        if (!authLoading && sellerId && token) fetchLogs();
    }, [authLoading, sellerId, token, fetchLogs]);

    const filteredLogs = logs.filter(
        (l) =>
            !searchQuery ||
            l.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
            l.item_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            l.details.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (authLoading || !sellerId) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400" />
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto p-4 md:p-8">
            {/* Header */}
            <header className="flex flex-col sm:flex-row items-start sm:items-center justify-between py-6 border-b border-[var(--border)] mb-6 gap-4">
                <div className="flex items-center gap-4">
                    <Link href="/dashboard" className="flex items-center gap-2 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors text-sm font-medium">
                        <ArrowLeft className="w-4 h-4" />
                        Dashboard
                    </Link>
                    <motion.h1 initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="text-2xl font-extrabold bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent tracking-tight">
                        📋 Activity & Webhook Logs
                    </motion.h1>
                </div>
                <button onClick={fetchLogs} className="flex items-center gap-2 bg-green-500/10 border border-green-500/20 text-green-400 px-4 py-1.5 rounded-full font-semibold text-sm hover:bg-green-500/20 transition-all">
                    <RefreshCcw className="w-3.5 h-3.5" />
                    Refresh
                </button>
            </header>

            {/* Search */}
            <div className="relative mb-6">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
                <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search logs by action, item, or details..."
                    className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text-primary)] text-sm placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-green-500/30 transition-all"
                />
            </div>

            {/* Loading */}
            {loading && (
                <div className="flex items-center justify-center py-20">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-400" />
                </div>
            )}

            {/* Empty */}
            {!loading && filteredLogs.length === 0 && (
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-[var(--card-bg)] border border-[var(--border)] rounded-2xl p-12 text-center">
                    <MessageSquare className="w-12 h-12 text-[var(--text-muted)] mx-auto mb-4" />
                    <h3 className="text-lg font-bold text-[var(--text-primary)] mb-2">No logs found</h3>
                    <p className="text-sm text-[var(--text-muted)]">Activity and WhatsApp interactions will appear here.</p>
                </motion.div>
            )}

            {/* Log Entries */}
            {!loading && filteredLogs.length > 0 && (
                <div className="space-y-2">
                    <AnimatePresence>
                        {filteredLogs.map((log, i) => (
                            <motion.div
                                key={log.id}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.02 }}
                                className="flex items-start gap-4 p-4 bg-[var(--card-bg)] border border-[var(--border)] rounded-xl hover:shadow-lg transition-all"
                            >
                                <div className="mt-1">{actionIcon(log.action)}</div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 flex-wrap mb-1">
                                        {actionBadge(log.action)}
                                        {log.item_name && (
                                            <span className="text-sm font-semibold text-[var(--text-primary)]">{log.item_name}</span>
                                        )}
                                    </div>
                                    {log.details && (
                                        <p className="text-xs text-[var(--text-muted)] truncate">{log.details}</p>
                                    )}
                                </div>
                                <div className="flex items-center gap-1 text-[10px] text-[var(--text-muted)] shrink-0">
                                    <Clock className="w-3 h-3" />
                                    {timeAgo(log.created_at)}
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            )}
        </div>
    );
}
