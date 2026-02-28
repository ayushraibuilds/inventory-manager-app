"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, User, Lock, Mail, ArrowRight } from "lucide-react";
import { Toaster, toast } from "sonner";
import Link from "next/link";
import { useAuth } from "@/components/AuthProvider";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        const loadingToast = toast.loading("Signing in...");

        try {
            const res = await fetch(`${API_URL}/api/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });

            if (res.ok) {
                const data = await res.json();
                toast.success("Welcome back!", { id: loadingToast });
                login(data.token, data.seller_id);
            } else {
                const err = await res.json();
                toast.error(err.detail || "Invalid email or password", { id: loadingToast });
            }
        } catch {
            toast.error("Network error. Please try again.", { id: loadingToast });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-[var(--bg-primary)]">
            <Toaster theme="dark" position="top-center" />

            <div className="w-full max-w-md">
                <Link href="/" className="inline-flex items-center gap-2 text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors mb-8">
                    <ArrowLeft className="w-4 h-4" /> Back to Home
                </Link>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-[var(--card-bg)] border border-[var(--border)] rounded-2xl p-6 sm:p-8 shadow-2xl"
                >
                    <div className="text-center mb-8">
                        <div className="w-12 h-12 bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-center justify-center mx-auto mb-4">
                            <Lock className="w-6 h-6 text-blue-400" />
                        </div>
                        <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-2">Welcome Back</h1>
                        <p className="text-sm text-[var(--text-secondary)]">Sign in to manage your ONDC store</p>
                    </div>

                    <form onSubmit={handleLogin} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">Email</label>
                            <div className="relative">
                                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
                                <input
                                    type="email"
                                    required
                                    value={email}
                                    onChange={e => setEmail(e.target.value)}
                                    className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-xl pl-10 pr-4 py-3 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-blue-500/50 transition-colors"
                                    placeholder="you@example.com"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">Password</label>
                            <div className="relative">
                                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
                                <input
                                    type="password"
                                    required
                                    value={password}
                                    onChange={e => setPassword(e.target.value)}
                                    className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-xl pl-10 pr-4 py-3 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-blue-500/50 transition-colors"
                                    placeholder="••••••••"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 mt-6 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white font-medium rounded-xl transition-all shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2"
                        >
                            {loading ? "Signing in..." : <>Sign In <ArrowRight className="w-4 h-4" /></>}
                        </button>
                    </form>

                    <p className="text-center text-sm text-[var(--text-muted)] mt-8">
                        Don't have an account? <Link href="/signup" className="text-blue-400 hover:text-blue-300 font-medium">Sign up</Link>
                    </p>
                </motion.div>
            </div>
        </div>
    );
}
