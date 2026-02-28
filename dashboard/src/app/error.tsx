"use client";

import { motion } from "framer-motion";
import { AlertTriangle, RotateCcw } from "lucide-react";

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    return (
        <div className="flex items-center justify-center min-h-screen p-6">
            <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                className="max-w-md w-full bg-[var(--card-bg)] border border-[var(--border)] rounded-2xl p-8 shadow-2xl text-center"
            >
                <div className="mx-auto w-14 h-14 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-5">
                    <AlertTriangle className="w-7 h-7 text-red-400" />
                </div>
                <h2 className="text-xl font-bold text-[var(--text-primary)] mb-2">Something went wrong</h2>
                <p className="text-sm text-[var(--text-secondary)] mb-6 leading-relaxed">
                    {error.message || "An unexpected error occurred. Please try again."}
                </p>
                <button
                    onClick={reset}
                    className="inline-flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white font-medium px-6 py-2.5 rounded-lg transition-all active:scale-95 shadow-lg shadow-blue-500/20"
                >
                    <RotateCcw className="w-4 h-4" />
                    Try Again
                </button>
            </motion.div>
        </div>
    );
}
