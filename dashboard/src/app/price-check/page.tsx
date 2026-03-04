"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    ArrowLeft,
    TrendingUp,
    TrendingDown,
    CheckCircle,
    AlertTriangle,
    DollarSign,
    RefreshCcw,
    BarChart3,
    Zap,
    Search,
    SlidersHorizontal,
} from "lucide-react";
import { Toaster, toast } from "sonner";
import Link from "next/link";
import { useAuth } from "@/components/AuthProvider";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PriceSuggestion {
    item_id: string;
    item_name: string;
    seller_price: number;
    market_avg: number;
    market_range: [number, number];
    unit: string;
    status: "competitive" | "high" | "low";
    suggestion: string;
}

interface PriceReport {
    seller_id: string;
    total_items: number;
    items_with_suggestions: number;
    suggestions: PriceSuggestion[];
}

export default function PriceCheckPage() {
    const { sellerId, token, isLoading: authLoading } = useAuth();
    const activeSellerId = sellerId || "";

    const [report, setReport] = useState<PriceReport | null>(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [batchUpdating, setBatchUpdating] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState<"all" | "competitive" | "high" | "low">("all");
    const [sortBy, setSortBy] = useState<"default" | "name" | "priceDiff" | "marketAvg">("default");

    const handleBatchUpdate = async () => {
        if (!report || !activeSellerId || !token) return;
        const nonCompetitive = report.suggestions.filter(s => s.status !== "competitive" && s.item_id);
        if (nonCompetitive.length === 0) {
            toast.info("All your prices are competitive!");
            return;
        }
        setBatchUpdating(true);
        try {
            const res = await fetch(`${API_URL}/api/catalog/batch-price-update`, {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify({
                    seller_id: activeSellerId,
                    updates: nonCompetitive.map(s => ({ item_id: s.item_id, new_price: String(s.market_avg) })),
                }),
            });
            if (!res.ok) throw new Error("Failed");
            const data = await res.json();
            toast.success(`Updated ${data.updated} prices to market rates!`);
            await fetchReport(false);
        } catch {
            toast.error("Failed to update prices.");
        } finally {
            setBatchUpdating(false);
        }
    };

    const fetchReport = useCallback(
        async (showToast = false) => {
            if (!activeSellerId || !token) return;
            try {
                if (showToast) setRefreshing(true);
                const res = await fetch(
                    `${API_URL}/api/v1/catalog/price-check?seller_id=${encodeURIComponent(activeSellerId)}`,
                    { headers: { Authorization: `Bearer ${token}` } }
                );
                if (res.status === 429) {
                    toast.error("Rate limit exceeded. Please wait.");
                    return;
                }
                if (!res.ok) throw new Error("Failed to fetch");
                const data: PriceReport = await res.json();
                setReport(data);
                if (showToast) toast.success("Report refreshed!");
            } catch {
                toast.error("Failed to load price intelligence.");
            } finally {
                setLoading(false);
                setRefreshing(false);
            }
        },
        [activeSellerId, token]
    );

    useEffect(() => {
        if (!authLoading && activeSellerId && token) fetchReport();
    }, [authLoading, activeSellerId, token, fetchReport]);

    const [isMounted, setIsMounted] = useState(false);
    useEffect(() => {
        setIsMounted(true);
    }, []);

    if (!isMounted || authLoading || !activeSellerId) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
            </div>
        );
    }

    const statusIcon = (status: string) => {
        switch (status) {
            case "competitive":
                return <CheckCircle className="w-5 h-5 text-emerald-400" />;
            case "high":
                return <TrendingUp className="w-5 h-5 text-amber-400" />;
            case "low":
                return <TrendingDown className="w-5 h-5 text-rose-400" />;
            default:
                return <AlertTriangle className="w-5 h-5 text-gray-400" />;
        }
    };

    const statusColor = (status: string) => {
        switch (status) {
            case "competitive":
                return "border-emerald-500/30 bg-emerald-500/5";
            case "high":
                return "border-amber-500/30 bg-amber-500/5";
            case "low":
                return "border-rose-500/30 bg-rose-500/5";
            default:
                return "border-[var(--border)] bg-[var(--card-bg)]";
        }
    };

    const statusLabel = (status: string) => {
        switch (status) {
            case "competitive":
                return (
                    <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                        ✅ COMPETITIVE
                    </span>
                );
            case "high":
                return (
                    <span className="text-xs font-bold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full">
                        ⬆️ ABOVE MARKET
                    </span>
                );
            case "low":
                return (
                    <span className="text-xs font-bold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded-full">
                        ⬇️ BELOW MARKET
                    </span>
                );
            default:
                return null;
        }
    };

    // Stats
    const competitive = report?.suggestions.filter((s) => s.status === "competitive").length || 0;
    const high = report?.suggestions.filter((s) => s.status === "high").length || 0;
    const low = report?.suggestions.filter((s) => s.status === "low").length || 0;

    // Filtered + sorted suggestions
    const filteredSuggestions = (report?.suggestions || [])
        .filter((s) => {
            if (statusFilter !== "all" && s.status !== statusFilter) return false;
            if (searchQuery && !s.item_name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
            return true;
        })
        .sort((a, b) => {
            switch (sortBy) {
                case "name": return a.item_name.localeCompare(b.item_name);
                case "priceDiff": return Math.abs(b.seller_price - b.market_avg) - Math.abs(a.seller_price - a.market_avg);
                case "marketAvg": return b.market_avg - a.market_avg;
                default: return 0;
            }
        });

    return (
        <div className="max-w-5xl mx-auto p-4 md:p-8">
            <Toaster theme="dark" position="top-center" />

            {/* Header */}
            <header className="flex flex-col sm:flex-row items-start sm:items-center justify-between py-6 border-b border-[var(--border)] mb-8 gap-4">
                <div className="flex items-center gap-4">
                    <Link
                        href="/dashboard"
                        className="flex items-center gap-2 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors text-sm font-medium"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Dashboard
                    </Link>
                    <motion.h1
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-2xl font-extrabold bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent tracking-tight"
                    >
                        💰 Price Intelligence
                    </motion.h1>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                    {report && report.suggestions.some(s => s.status !== "competitive") && (
                        <button
                            onClick={handleBatchUpdate}
                            disabled={batchUpdating}
                            className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-4 py-1.5 rounded-full font-semibold text-sm hover:bg-emerald-500/20 transition-all disabled:opacity-50"
                        >
                            <Zap className={`w-3.5 h-3.5 ${batchUpdating ? "animate-pulse" : ""}`} />
                            {batchUpdating ? "Updating..." : "Match Market Prices"}
                        </button>
                    )}
                    <button
                        onClick={() => fetchReport(true)}
                        disabled={refreshing}
                        className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/20 text-amber-400 px-4 py-1.5 rounded-full font-semibold text-sm hover:bg-amber-500/20 transition-all disabled:opacity-50"
                    >
                        <RefreshCcw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
                        {refreshing ? "Refreshing..." : "Refresh"}
                    </button>
                </div>
            </header>

            {/* Summary Stats */}
            {report && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8"
                >
                    <div className="bg-[var(--card-bg)] backdrop-blur-xl border border-[var(--border)] rounded-2xl p-5 text-center shadow-lg">
                        <p className="text-3xl font-bold text-[var(--text-primary)]">{report.total_items}</p>
                        <p className="text-xs text-[var(--text-muted)] mt-1 font-medium">Total Items</p>
                    </div>
                    <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-2xl p-5 text-center shadow-lg">
                        <p className="text-3xl font-bold text-emerald-400">{competitive}</p>
                        <p className="text-xs text-emerald-400/70 mt-1 font-medium">Competitive</p>
                    </div>
                    <div className="bg-amber-500/5 border border-amber-500/20 rounded-2xl p-5 text-center shadow-lg">
                        <p className="text-3xl font-bold text-amber-400">{high}</p>
                        <p className="text-xs text-amber-400/70 mt-1 font-medium">Above Market</p>
                    </div>
                    <div className="bg-rose-500/5 border border-rose-500/20 rounded-2xl p-5 text-center shadow-lg">
                        <p className="text-3xl font-bold text-rose-400">{low}</p>
                        <p className="text-xs text-rose-400/70 mt-1 font-medium">Below Market</p>
                    </div>
                </motion.div>
            )}

            {/* Loading */}
            {loading && (
                <div className="flex items-center justify-center py-20">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-400"></div>
                </div>
            )}

            {/* Empty State */}
            {!loading && report && report.suggestions.length === 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-[var(--card-bg)] backdrop-blur-xl border border-[var(--border)] rounded-2xl p-12 text-center shadow-2xl"
                >
                    <BarChart3 className="w-12 h-12 text-[var(--text-muted)] mx-auto mb-4" />
                    <h3 className="text-lg font-bold text-[var(--text-primary)] mb-2">No Price Data Available</h3>
                    <p className="text-sm text-[var(--text-muted)]">
                        {report.total_items === 0
                            ? "Add products to your catalog first, then check back for market comparisons."
                            : "Your products don't match our price reference database yet. We're constantly expanding coverage."}
                    </p>
                </motion.div>
            )}

            {/* Search / Filter / Sort Bar */}
            {!loading && report && report.suggestions.length > 0 && (
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 mb-6">
                    {/* Search Input */}
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search by product name..."
                            className="w-full pl-9 pr-4 py-2 rounded-xl bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text-primary)] text-sm placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:border-amber-500/40 transition-all"
                        />
                    </div>

                    {/* Status Filter Tabs */}
                    <div className="flex items-center gap-1 bg-[var(--card-bg)] border border-[var(--border)] rounded-xl p-1">
                        {(["all", "competitive", "high", "low"] as const).map((f) => (
                            <button
                                key={f}
                                onClick={() => setStatusFilter(f)}
                                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${statusFilter === f
                                        ? f === "all" ? "bg-[var(--bg-primary)] text-[var(--text-primary)]"
                                            : f === "competitive" ? "bg-emerald-500/20 text-emerald-400"
                                                : f === "high" ? "bg-amber-500/20 text-amber-400"
                                                    : "bg-rose-500/20 text-rose-400"
                                        : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                                    }`}
                            >
                                {f === "all" ? "All" : f === "competitive" ? "✅" : f === "high" ? "⬆️" : "⬇️"}
                                {" "}
                                {f === "all" ? report.suggestions.length
                                    : f === "competitive" ? competitive
                                        : f === "high" ? high : low}
                            </button>
                        ))}
                    </div>

                    {/* Sort Dropdown */}
                    <div className="relative">
                        <SlidersHorizontal className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-muted)]" />
                        <select
                            value={sortBy}
                            onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                            className="pl-9 pr-8 py-2 rounded-xl bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text-primary)] text-sm appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-amber-500/30"
                        >
                            <option value="default">Default</option>
                            <option value="name">Name A→Z</option>
                            <option value="priceDiff">Biggest Diff</option>
                            <option value="marketAvg">Market Avg ↓</option>
                        </select>
                    </div>
                </div>
            )}

            {/* Item Cards */}
            {!loading && filteredSuggestions.length > 0 && (
                <div className="space-y-4">
                    <AnimatePresence>
                        {filteredSuggestions.map((item, i) => {
                            const range = item.market_range[1] - item.market_range[0];
                            const positionPct = range > 0 ? Math.min(100, Math.max(0, ((item.seller_price - item.market_range[0]) / range) * 100)) : 50;

                            return (
                                <motion.div
                                    key={`${item.item_name}-${i}`}
                                    initial={{ opacity: 0, y: 15 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: i * 0.05 }}
                                    className={`border rounded-2xl p-5 shadow-lg transition-all hover:shadow-xl ${statusColor(item.status)}`}
                                >
                                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                                        <div className="flex items-center gap-3">
                                            {statusIcon(item.status)}
                                            <div>
                                                <h3 className="text-base font-bold text-[var(--text-primary)] capitalize">{item.item_name}</h3>
                                                <p className="text-xs text-[var(--text-muted)]">per {item.unit}</p>
                                            </div>
                                        </div>
                                        {statusLabel(item.status)}
                                    </div>

                                    {/* Price Comparison */}
                                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 mb-4">
                                        <div className="flex sm:block justify-between sm:text-center">
                                            <p className="text-xs text-[var(--text-muted)] mb-0 sm:mb-1">Your Price</p>
                                            <p className="text-lg sm:text-xl font-bold text-[var(--text-primary)]">₹{item.seller_price}</p>
                                        </div>
                                        <div className="flex sm:block justify-between sm:text-center">
                                            <p className="text-xs text-[var(--text-muted)] mb-0 sm:mb-1">Market Avg</p>
                                            <p className="text-lg sm:text-xl font-bold text-blue-400">₹{item.market_avg}</p>
                                        </div>
                                        <div className="flex sm:block justify-between sm:text-center">
                                            <p className="text-xs text-[var(--text-muted)] mb-0 sm:mb-1">Market Range</p>
                                            <p className="text-lg sm:text-xl font-bold text-[var(--text-secondary)]">
                                                ₹{item.market_range[0]}–{item.market_range[1]}
                                            </p>
                                        </div>
                                    </div>

                                    {/* Visual Range Bar */}
                                    <div className="relative h-2.5 bg-[var(--bg-primary)] rounded-full overflow-hidden mb-2">
                                        {/* Market range fill */}
                                        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 via-blue-500/30 to-blue-500/20 rounded-full" />
                                        {/* Market avg marker */}
                                        <div
                                            className="absolute top-0 bottom-0 w-0.5 bg-blue-400/60"
                                            style={{ left: `${range > 0 ? ((item.market_avg - item.market_range[0]) / range) * 100 : 50}%` }}
                                        />
                                        {/* Seller price marker */}
                                        <div
                                            className={`absolute top-0 h-full w-3 rounded-full shadow-lg ${item.status === "competitive"
                                                ? "bg-emerald-400"
                                                : item.status === "high"
                                                    ? "bg-amber-400"
                                                    : "bg-rose-400"
                                                }`}
                                            style={{ left: `${Math.max(0, Math.min(97, positionPct))}%` }}
                                        />
                                    </div>
                                    <div className="flex justify-between text-xs text-[var(--text-muted)]">
                                        <span>₹{item.market_range[0]}</span>
                                        <span>₹{item.market_range[1]}</span>
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
