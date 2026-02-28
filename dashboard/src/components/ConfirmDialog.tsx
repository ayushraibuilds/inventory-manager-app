"use client";

import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle } from "lucide-react";

interface ConfirmDialogProps {
    isOpen: boolean;
    title: string;
    message: string;
    confirmLabel?: string;
    onConfirm: () => void;
    onCancel: () => void;
}

export default function ConfirmDialog({
    isOpen,
    title,
    message,
    confirmLabel = "Delete",
    onConfirm,
    onCancel
}: ConfirmDialogProps) {
    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                        onClick={onCancel}
                    />
                    <motion.div
                        initial={{ scale: 0.95, opacity: 0, y: 10 }}
                        animate={{ scale: 1, opacity: 1, y: 0 }}
                        exit={{ scale: 0.95, opacity: 0, y: 10 }}
                        className="relative w-full max-w-sm bg-[var(--bg-primary)] border border-[var(--border)] rounded-2xl shadow-2xl overflow-hidden"
                    >
                        <div className="p-6 text-center">
                            <div className="mx-auto w-12 h-12 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-4">
                                <AlertTriangle className="w-6 h-6 text-red-400" />
                            </div>
                            <h3 className="text-lg font-bold text-[var(--text-primary)] mb-2">{title}</h3>
                            <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{message}</p>
                        </div>
                        <div className="flex border-t border-[var(--border)]">
                            <button
                                onClick={onCancel}
                                className="flex-1 py-3 text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--card-hover)] transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={onConfirm}
                                className="flex-1 py-3 text-sm font-bold text-red-400 hover:bg-red-500/10 border-l border-[var(--border)] transition-colors"
                            >
                                {confirmLabel}
                            </button>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}
