"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, BarChart3, Package, TrendingUp, PieChart as PieIcon, ChevronDown } from "lucide-react";
import { Toaster, toast } from "sonner";
import Link from "next/link";
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
    PieChart, Pie, Cell,
    ResponsiveContainer
} from "recharts";
import { useAuth } from "@/components/AuthProvider";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AnalyticsData {
    total_products: number;
    total_value: number;
    categories: { name: string; count: number; value: number }[];
    top_items: { name: string; value: number; quantity: number; price: number }[];
    price_distribution: { name: string; price: number; quantity: number }[];
    stock_status: { name: string; value: number; fill: string }[];
}

const CHART_COLORS = ["#58a6ff", "#f78166", "#8b5cf6", "#22c55e", "#eab308", "#ec4899", "#06b6d4"];

export default function AnalyticsPage() {
    const { sellerId, isLoading: authLoading } = useAuth();
    const activeSellerId = sellerId || "";

    const [data, setData] = useState<AnalyticsData | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchAnalytics = useCallback(async () => {
        if (!activeSellerId) return;
        setLoading(true);
        try {
            const res = await fetch(`${API_URL}/api/analytics?seller_id=${encodeURIComponent(activeSellerId)}`);
            if (res.status === 429) { toast.error("Rate limit exceeded. Please try again later."); return; }
            if (res.ok) {
                setData(await res.json());
            }
        } catch {
            console.error("Failed to fetch analytics");
        } finally {
            setLoading(false);
        }
    }, [activeSellerId]);

    useEffect(() => {
        if (!authLoading && activeSellerId) fetchAnalytics();
    }, [fetchAnalytics, authLoading, activeSellerId]);

    const [isMounted, setIsMounted] = useState(false);
    useEffect(() => { setIsMounted(true); }, []);

    if (!isMounted || loading || authLoading || !activeSellerId) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="flex items-center justify-center min-h-screen text-gray-400">
                Failed to load analytics.
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto p-4 md:p-8">
            <Toaster theme="dark" position="top-center" />

            {/* Header */}
            <header className="flex items-center justify-between py-6 border-b border-[var(--border)] mb-8">
                <div className="flex items-center gap-4">
                    <Link
                        href="/dashboard"
                        className="flex items-center gap-2 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors text-sm font-medium"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Back to Dashboard
                    </Link>
                    <motion.h1
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-2xl font-extrabold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent tracking-tight"
                    >
                        Analytics
                    </motion.h1>
                </div>
            </header>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0 }}
                    className="bg-[#161b22]/80 backdrop-blur-xl border border-white/5 rounded-2xl p-5 shadow-2xl">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-9 h-9 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                            <Package className="w-4.5 h-4.5 text-blue-400" />
                        </div>
                        <span className="text-sm text-gray-400 font-medium">Total Products</span>
                    </div>
                    <p className="text-3xl font-extrabold text-white">{data.total_products}</p>
                </motion.div>

                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}
                    className="bg-[#161b22]/80 backdrop-blur-xl border border-white/5 rounded-2xl p-5 shadow-2xl">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-9 h-9 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center justify-center">
                            <TrendingUp className="w-4.5 h-4.5 text-green-400" />
                        </div>
                        <span className="text-sm text-gray-400 font-medium">Total Inventory Value</span>
                    </div>
                    <p className="text-3xl font-extrabold text-white">₹{data.total_value.toLocaleString()}</p>
                </motion.div>

                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
                    className="bg-[#161b22]/80 backdrop-blur-xl border border-white/5 rounded-2xl p-5 shadow-2xl">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-9 h-9 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
                            <BarChart3 className="w-4.5 h-4.5 text-purple-400" />
                        </div>
                        <span className="text-sm text-gray-400 font-medium">Categories</span>
                    </div>
                    <p className="text-3xl font-extrabold text-white">{data.categories.length}</p>
                </motion.div>
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Top Items by Value */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
                    className="bg-[#161b22]/80 backdrop-blur-xl border border-white/5 rounded-2xl p-6 shadow-2xl">
                    <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                        <BarChart3 className="w-4.5 h-4.5 text-blue-400" />
                        Top Items by Inventory Value
                    </h3>
                    {data.top_items.length > 0 ? (
                        <ResponsiveContainer width="100%" height={280}>
                            <BarChart data={data.top_items.slice(0, 8)} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                <XAxis dataKey="name" tick={{ fill: "#6b7280", fontSize: 11 }} tickFormatter={(v) => v.length > 10 ? v.slice(0, 10) + "…" : v} />
                                <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} tickFormatter={(v) => `₹${v}`} />
                                <Tooltip
                                    contentStyle={{ background: "#0d1117", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "12px", fontSize: "12px" }}
                                    labelStyle={{ color: "#fff" }}
                                    formatter={(value: any) => [`₹${Number(value).toLocaleString()}`, "Value"]}
                                />
                                <Bar dataKey="value" fill="#58a6ff" radius={[6, 6, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="flex items-center justify-center h-64 text-gray-500 text-sm">No data available</div>
                    )}
                </motion.div>

                {/* Category Breakdown */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
                    className="bg-[#161b22]/80 backdrop-blur-xl border border-white/5 rounded-2xl p-6 shadow-2xl">
                    <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                        <PieIcon className="w-4.5 h-4.5 text-purple-400" />
                        Category Breakdown
                    </h3>
                    {data.categories.length > 0 ? (
                        <div className="flex items-center justify-center">
                            <ResponsiveContainer width="100%" height={280}>
                                <PieChart>
                                    <Pie
                                        data={data.categories}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={100}
                                        paddingAngle={3}
                                        dataKey="count"
                                        nameKey="name"
                                        label={({ name, payload }: any) => `${name} (${payload?.count ?? 0})`}
                                    >
                                        {data.categories.map((_entry, index) => (
                                            <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        contentStyle={{ background: "#0d1117", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "12px", fontSize: "12px" }}
                                        formatter={(value: any) => [value, "Products"]}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <div className="flex items-center justify-center h-64 text-gray-500 text-sm">No data available</div>
                    )}
                </motion.div>

                {/* Stock Health */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}
                    className="bg-[#161b22]/80 backdrop-blur-xl border border-white/5 rounded-2xl p-6 shadow-2xl">
                    <h3 className="text-base font-bold text-white mb-4">Stock Health</h3>
                    <div className="flex items-center justify-center">
                        <ResponsiveContainer width="100%" height={280}>
                            <PieChart>
                                <Pie
                                    data={data.stock_status}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={55}
                                    outerRadius={95}
                                    paddingAngle={5}
                                    dataKey="value"
                                    nameKey="name"
                                    label={({ name, value }) => value > 0 ? `${name}: ${value}` : ""}
                                >
                                    {data.stock_status.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.fill} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ background: "#0d1117", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "12px", fontSize: "12px" }}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="flex justify-center gap-6 mt-2">
                        {data.stock_status.map(s => (
                            <div key={s.name} className="flex items-center gap-2 text-xs">
                                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: s.fill }} />
                                <span className="text-gray-400">{s.name}</span>
                            </div>
                        ))}
                    </div>
                </motion.div>

                {/* Price Distribution */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
                    className="bg-[#161b22]/80 backdrop-blur-xl border border-white/5 rounded-2xl p-6 shadow-2xl">
                    <h3 className="text-base font-bold text-white mb-4">Price Distribution</h3>
                    {data.price_distribution.length > 0 ? (
                        <ResponsiveContainer width="100%" height={280}>
                            <BarChart data={data.price_distribution} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                <XAxis dataKey="name" tick={{ fill: "#6b7280", fontSize: 10 }} tickFormatter={(v) => v.length > 8 ? v.slice(0, 8) + "…" : v} />
                                <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} tickFormatter={(v) => `₹${v}`} />
                                <Tooltip
                                    contentStyle={{ background: "#0d1117", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "12px", fontSize: "12px" }}
                                    labelStyle={{ color: "#fff" }}
                                    formatter={(value: any) => [`₹${value}`, "Price"]}
                                />
                                <Bar dataKey="price" fill="#f78166" radius={[6, 6, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="flex items-center justify-center h-64 text-gray-500 text-sm">No data available</div>
                    )}
                </motion.div>
            </div>
        </div>
    );
}
