"use client";
import { useEffect } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, RefreshCw } from "lucide-react";

export default function OrdersError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
    useEffect(() => { console.error(error); }, [error]);

    return (
        <div className="flex items-center justify-center min-h-screen p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center max-w-md"
            >
                <div className="mx-auto w-16 h-16 rounded-full bg-orange-500/10 border border-orange-500/20 flex items-center justify-center mb-6">
                    <AlertTriangle className="w-8 h-8 text-orange-400" />
                </div>
                <h2 className="text-xl font-bold text-[var(--text-primary)] mb-2">Orders Error</h2>
                <p className="text-sm text-[var(--text-secondary)] mb-6">{error.message}</p>
                <button
                    onClick={reset}
                    className="inline-flex items-center gap-2 px-6 py-2.5 bg-orange-500/10 border border-orange-500/20 text-orange-400 rounded-xl font-semibold text-sm hover:bg-orange-500/20 transition-all"
                >
                    <RefreshCw className="w-4 h-4" />
                    Try Again
                </button>
            </motion.div>
        </div>
    );
}
