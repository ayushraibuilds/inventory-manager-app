"use client";

import { useEffect } from "react";
import { AlertTriangle, RefreshCcw, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function PriceCheckError({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        console.error("Price Intelligence error:", error);
    }, [error]);

    return (
        <div className="max-w-5xl mx-auto p-4 md:p-8">
            <header className="flex items-center gap-4 py-6 border-b border-[var(--border)] mb-8">
                <Link
                    href="/dashboard"
                    className="flex items-center gap-2 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors text-sm font-medium"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Dashboard
                </Link>
                <h1 className="text-2xl font-extrabold text-[var(--text-primary)]">
                    💰 Price Intelligence
                </h1>
            </header>

            <div className="bg-rose-500/5 border border-rose-500/20 rounded-2xl p-12 text-center shadow-2xl">
                <AlertTriangle className="w-12 h-12 text-rose-400 mx-auto mb-4" />
                <h3 className="text-lg font-bold text-[var(--text-primary)] mb-2">
                    Something went wrong
                </h3>
                <p className="text-sm text-[var(--text-muted)] mb-6 max-w-md mx-auto">
                    We couldn&apos;t load the price intelligence report. This could be a
                    temporary issue with the server connection.
                </p>
                <button
                    onClick={reset}
                    className="flex items-center gap-2 mx-auto bg-rose-500/10 border border-rose-500/20 text-rose-400 px-5 py-2 rounded-full font-semibold text-sm hover:bg-rose-500/20 transition-all"
                >
                    <RefreshCcw className="w-3.5 h-3.5" />
                    Try Again
                </button>
            </div>
        </div>
    );
}
