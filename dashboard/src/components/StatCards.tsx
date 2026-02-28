import { motion } from "framer-motion";

interface StatCardsProps {
    totalProducts: number;
    totalValue: number;
    lowStockCount: number;
}

export default function StatCards({ totalProducts, totalValue, lowStockCount }: StatCardsProps) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-[var(--card-bg)] backdrop-blur-xl border border-[var(--border)] rounded-2xl p-6 shadow-xl flex flex-col gap-2 transition-colors"
            >
                <span className="text-[var(--text-muted)] text-sm font-medium tracking-wide">Total Products</span>
                <span className="text-3xl font-extrabold text-[var(--text-primary)]">{totalProducts}</span>
            </motion.div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="bg-[var(--card-bg)] backdrop-blur-xl border border-[var(--border)] rounded-2xl p-6 shadow-xl flex flex-col gap-2 transition-colors"
            >
                <span className="text-[var(--text-muted)] text-sm font-medium tracking-wide">Total Value (INR)</span>
                <span className="text-3xl font-extrabold text-[var(--text-primary)]">₹{totalValue.toLocaleString('en-IN')}</span>
            </motion.div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className={`bg-[var(--card-bg)] backdrop-blur-xl border rounded-2xl p-6 shadow-xl flex flex-col gap-2 transition-colors ${lowStockCount > 0
                    ? "border-red-500/30 bg-red-500/5 relative overflow-hidden"
                    : "border-[var(--border)]"
                    }`}
            >
                {lowStockCount > 0 && (
                    <div className="absolute top-0 left-0 w-full h-1 bg-red-500/50"></div>
                )}
                <span className="text-sm font-medium tracking-wide flex items-center justify-between">
                    <span className={lowStockCount > 0 ? "text-red-400" : "text-[var(--text-muted)]"}>Low Stock Alerts</span>
                    {lowStockCount > 0 && <span className="flex h-2.5 w-2.5 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)] animate-pulse"></span>}
                </span>
                <span className={`text-3xl font-extrabold ${lowStockCount > 0 ? "text-red-500" : "text-[var(--text-primary)]"}`}>
                    {lowStockCount}
                </span>
            </motion.div>
        </div>
    );
}
