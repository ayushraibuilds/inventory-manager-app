"use client";
import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Package, Clock, CheckCircle, Truck, XCircle, RefreshCw, ChevronDown, Search, Calendar, Download } from "lucide-react";
import { Toaster, toast } from "sonner";
import Link from "next/link";
import { useAuth } from "@/components/AuthProvider";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

interface OrderItem {
    name?: string;
    quantity?: number;
    price?: number;
}

interface Order {
    id: string;
    seller_id: string;
    buyer_name: string;
    buyer_phone: string;
    items: OrderItem[];
    total_amount: number;
    status: string;
    created_at: string;
    updated_at: string;
}

const STATUS_CONFIG: Record<string, { badgeClass: string; icon: React.ReactNode; label: string }> = {
    PLACED: { badgeClass: "bg-blue-500/10 text-blue-400 border-blue-500/20", icon: <Clock className="w-3.5 h-3.5" />, label: "Placed" },
    ACCEPTED: { badgeClass: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20", icon: <CheckCircle className="w-3.5 h-3.5" />, label: "Accepted" },
    SHIPPED: { badgeClass: "bg-purple-500/10 text-purple-400 border-purple-500/20", icon: <Truck className="w-3.5 h-3.5" />, label: "Shipped" },
    DELIVERED: { badgeClass: "bg-green-500/10 text-green-400 border-green-500/20", icon: <CheckCircle className="w-3.5 h-3.5" />, label: "Delivered" },
    CANCELLED: { badgeClass: "bg-red-500/10 text-red-400 border-red-500/20", icon: <XCircle className="w-3.5 h-3.5" />, label: "Cancelled" },
};

const NEXT_STATUS: Record<string, string> = {
    PLACED: "ACCEPTED",
    ACCEPTED: "SHIPPED",
    SHIPPED: "DELIVERED",
};

export default function OrdersPage() {
    const { sellerId, token, isLoading } = useAuth();
    const activeSellerId = sellerId || "";

    const [orders, setOrders] = useState<Order[]>([]);
    const [loading, setLoading] = useState(true);
    const [filterStatus, setFilterStatus] = useState("all");
    const [showFilterDropdown, setShowFilterDropdown] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [dateFrom, setDateFrom] = useState("");
    const [dateTo, setDateTo] = useState("");

    const fetchOrders = useCallback(async () => {
        if (!activeSellerId || !token) return;
        try {
            const params = new URLSearchParams();
            params.set("seller_id", activeSellerId);
            if (filterStatus !== "all") params.set("status", filterStatus);
            if (searchQuery.trim()) params.set("search", searchQuery.trim());
            if (dateFrom) params.set("date_from", dateFrom);
            if (dateTo) params.set("date_to", dateTo);

            const res = await fetch(`${API_URL}/api/orders?${params.toString()}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (res.status === 429) { toast.error("Rate limit exceeded."); return; }
            if (res.ok) {
                const data = await res.json();
                setOrders(data.orders || []);
            }
        } catch { toast.error("Failed to load orders."); }
        finally { setLoading(false); }
    }, [filterStatus, activeSellerId, searchQuery, dateFrom, dateTo, token]);

    useEffect(() => {
        if (!isLoading && activeSellerId && token) fetchOrders();
    }, [fetchOrders, isLoading, activeSellerId, token]);

    const updateStatus = async (orderId: string, newStatus: string) => {
        const loadingToast = toast.loading(`Updating to ${newStatus}...`);
        try {
            const res = await fetch(`${API_URL}/api/orders/${orderId}/status`, {
                method: "PUT",
                headers: { "Content-Type": "application/json", "X-API-Key": API_KEY , "Authorization": `Bearer ${token}` },
                body: JSON.stringify({ status: newStatus }),
            });
            if (res.status === 429) { toast.error("Rate limit exceeded.", { id: loadingToast }); return; }
            if (res.ok) {
                toast.success(`Order updated to ${newStatus}.`, { id: loadingToast });
                fetchOrders();
            } else {
                toast.error("Failed to update order.", { id: loadingToast });
            }
        } catch { toast.error("Network error.", { id: loadingToast }); }
    };

    const exportCSV = () => {
        if (orders.length === 0) { toast.error("No orders to export."); return; }
        const headers = ["Order ID", "Buyer", "Phone", "Items", "Total (₹)", "Status", "Created"];
        const rows = orders.map(o => [
            o.id,
            o.buyer_name || "Unknown",
            o.buyer_phone || "",
            o.items.map(i => `${i.name || "Item"} x${i.quantity || 1}`).join("; "),
            o.total_amount.toString(),
            o.status,
            new Date(o.created_at).toLocaleDateString("en-IN"),
        ]);
        const csv = [headers, ...rows].map(r => r.map(c => `"${c}"`).join(",")).join("\n");
        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `orders_${new Date().toISOString().split("T")[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        toast.success("Orders exported as CSV");
    };

    const timeAgo = (ts: string) => {
        const diff = Date.now() - new Date(ts).getTime();
        const mins = Math.floor(diff / 60000);
        if (mins < 60) return `${mins}m ago`;
        const hrs = Math.floor(mins / 60);
        if (hrs < 24) return `${hrs}h ago`;
        return `${Math.floor(hrs / 24)}d ago`;
    };

    if (isLoading || !activeSellerId) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
            </div>
        );
    }

    return (
        <div className="max-w-5xl mx-auto p-4 md:p-8">
            <Toaster theme="dark" position="top-center" />

            <header className="flex items-center justify-between py-6 border-b border-[var(--border)] mb-6">
                <div className="flex items-center gap-4">
                    <Link href="/dashboard" className="flex items-center justify-center w-9 h-9 rounded-lg bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">
                        <ArrowLeft className="w-4 h-4" />
                    </Link>
                    <motion.h1
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="text-2xl font-extrabold bg-gradient-to-r from-orange-400 to-red-400 bg-clip-text text-transparent"
                    >
                        Orders
                    </motion.h1>
                    <span className="text-xs text-[var(--text-muted)] bg-[var(--card-bg)] px-2.5 py-1 rounded-full border border-[var(--border)]">{orders.length} total</span>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={exportCSV} className="flex items-center gap-1.5 bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text-secondary)] px-3 py-1.5 rounded-lg text-xs font-medium hover:text-[var(--text-primary)] transition-all" title="Export CSV">
                        <Download className="w-3.5 h-3.5" /> Export
                    </button>
                    <button onClick={() => fetchOrders()} className="flex items-center justify-center w-9 h-9 rounded-lg bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
            </header>

            {/* Filters Bar */}
            <div className="flex flex-wrap items-center gap-3 mb-6">
                {/* Search */}
                <div className="relative flex-1 min-w-[180px]">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
                    <input
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                        onKeyDown={e => e.key === "Enter" && fetchOrders()}
                        placeholder="Search buyer, order ID..."
                        className="w-full bg-[var(--card-bg)] border border-[var(--border)] rounded-lg pl-9 pr-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-orange-500/50"
                    />
                </div>

                {/* Date From */}
                <div className="relative">
                    <Calendar className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-muted)]" />
                    <input
                        type="date"
                        value={dateFrom}
                        onChange={e => setDateFrom(e.target.value)}
                        className="bg-[var(--card-bg)] border border-[var(--border)] rounded-lg pl-8 pr-2 py-2 text-xs text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-orange-500/50"
                    />
                </div>
                <span className="text-xs text-[var(--text-muted)]">to</span>
                <div className="relative">
                    <Calendar className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-muted)]" />
                    <input
                        type="date"
                        value={dateTo}
                        onChange={e => setDateTo(e.target.value)}
                        className="bg-[var(--card-bg)] border border-[var(--border)] rounded-lg pl-8 pr-2 py-2 text-xs text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-orange-500/50"
                    />
                </div>

                {/* Status Filter */}
                <div className="relative">
                    <button
                        onClick={() => setShowFilterDropdown(!showFilterDropdown)}
                        className="flex items-center gap-2 bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text-primary)] px-4 py-2 rounded-lg text-xs font-medium hover:bg-[var(--card-hover)] transition-all"
                    >
                        {filterStatus === "all" ? "All Status" : STATUS_CONFIG[filterStatus]?.label || filterStatus}
                        <ChevronDown className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                    </button>
                    {showFilterDropdown && (
                        <motion.div
                            initial={{ opacity: 0, y: -5 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="absolute right-0 top-full mt-2 w-44 bg-[var(--bg-primary)] border border-[var(--border)] rounded-xl shadow-2xl z-50 overflow-hidden"
                        >
                            {["all", "PLACED", "ACCEPTED", "SHIPPED", "DELIVERED", "CANCELLED"].map(s => (
                                <button
                                    key={s}
                                    onClick={() => { setFilterStatus(s); setShowFilterDropdown(false); }}
                                    className={`w-full text-left px-4 py-2.5 text-sm hover:bg-[var(--card-hover)] transition-colors ${filterStatus === s ? "text-orange-400 font-semibold" : "text-[var(--text-secondary)]"}`}
                                >
                                    {s === "all" ? "All Status" : STATUS_CONFIG[s]?.label || s}
                                </button>
                            ))}
                        </motion.div>
                    )}
                </div>

                {(searchQuery || dateFrom || dateTo || filterStatus !== "all") && (
                    <button
                        onClick={() => { setSearchQuery(""); setDateFrom(""); setDateTo(""); setFilterStatus("all"); }}
                        className="text-xs text-orange-400 hover:text-orange-300 font-semibold"
                    >
                        Clear
                    </button>
                )}
            </div>

            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <RefreshCw className="w-8 h-8 animate-spin text-orange-400" />
                </div>
            ) : orders.length === 0 ? (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center py-20 border border-dashed border-[var(--border)] rounded-2xl bg-[var(--card-bg)]"
                >
                    <Package className="w-12 h-12 mx-auto mb-4 text-[var(--text-muted)]" />
                    <p className="text-lg font-medium text-[var(--text-primary)] mb-2">No orders yet</p>
                    <p className="text-sm text-[var(--text-secondary)]">Orders will appear here when buyers place them.</p>
                </motion.div>
            ) : (
                <div className="space-y-4">
                    <AnimatePresence mode="popLayout">
                        {orders.map((order, idx) => {
                            const cfg = STATUS_CONFIG[order.status] || STATUS_CONFIG.PLACED;
                            const nextStatus = NEXT_STATUS[order.status];
                            return (
                                <motion.div
                                    key={order.id}
                                    layout
                                    initial={{ opacity: 0, y: 15 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, x: -20 }}
                                    transition={{ delay: idx * 0.05 }}
                                    className="bg-[var(--card-bg)] backdrop-blur-xl border border-[var(--border)] rounded-2xl p-5 shadow-lg"
                                >
                                    <div className="flex flex-col sm:flex-row justify-between gap-4">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-3 mb-3">
                                                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${cfg.badgeClass}`}>
                                                    {cfg.icon}
                                                    {cfg.label}
                                                </span>
                                                <span className="text-xs text-[var(--text-muted)] font-mono">{order.id.substring(0, 8)}</span>
                                                <span className="text-xs text-[var(--text-muted)]">{timeAgo(order.created_at)}</span>
                                            </div>
                                            <div className="mb-2">
                                                <span className="text-sm font-semibold text-[var(--text-primary)]">{order.buyer_name || "Unknown buyer"}</span>
                                                {order.buyer_phone && <span className="text-xs text-[var(--text-muted)] ml-2">{order.buyer_phone}</span>}
                                            </div>
                                            <div className="space-y-1">
                                                {order.items.map((item, i) => (
                                                    <div key={i} className="text-sm text-[var(--text-secondary)]">
                                                        • {item.name || "Item"} × {item.quantity || 1}
                                                        {item.price && <span className="text-[var(--text-muted)] ml-1">₹{item.price}</span>}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                        <div className="flex flex-col items-end justify-between gap-3">
                                            <span className="text-xl font-bold text-[var(--text-primary)]">₹{order.total_amount.toLocaleString("en-IN")}</span>
                                            <div className="flex gap-2">
                                                {nextStatus && (
                                                    <button
                                                        onClick={() => updateStatus(order.id, nextStatus)}
                                                        className="px-4 py-1.5 bg-orange-500/10 border border-orange-500/20 text-orange-400 rounded-lg text-xs font-semibold hover:bg-orange-500/20 transition-all"
                                                    >
                                                        → {STATUS_CONFIG[nextStatus]?.label}
                                                    </button>
                                                )}
                                                {order.status !== "CANCELLED" && order.status !== "DELIVERED" && (
                                                    <button
                                                        onClick={() => updateStatus(order.id, "CANCELLED")}
                                                        className="px-3 py-1.5 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-xs font-semibold hover:bg-red-500/20 transition-all"
                                                    >
                                                        Cancel
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            );
                        })}
                    </AnimatePresence>
                </div>
            )}
        </div>
    );
}
