"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, UserPlus, Lock, Mail, ArrowRight } from "lucide-react";
import { Toaster, toast } from "sonner";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SignupPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const router = useRouter();

    const handleSignup = async (e: React.FormEvent) => {
        e.preventDefault();

        if (password.length < 6) {
            toast.error("Password must be at least 6 characters");
            return;
        }

        setLoading(true);
        const loadingToast = toast.loading("Creating account...");

        try {
            const res = await fetch(`${API_URL}/api/auth/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });

            if (res.ok) {
                // Auto login after successful signup
                const loginRes = await fetch(`${API_URL}/api/auth/login`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password }),
                });

                if (loginRes.ok) {
                    const data = await loginRes.json();
                    toast.success("Account created successfully!", { id: loadingToast });
                    login(data.token, data.seller_id);
                    // Redirect new users to onboarding wizard
                    setTimeout(() => router.push("/onboarding"), 100);
                }
            } else {
                const err = await res.json();
                toast.error(err.detail || "Failed to create account", { id: loadingToast });
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
                        <div className="w-12 h-12 bg-purple-500/10 border border-purple-500/20 rounded-xl flex items-center justify-center mx-auto mb-4">
                            <UserPlus className="w-6 h-6 text-purple-400" />
                        </div>
                        <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-2">Create an Account</h1>
                        <p className="text-sm text-[var(--text-secondary)]">Join the ONDC Super Seller network</p>
                    </div>

                    <form onSubmit={handleSignup} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">Email</label>
                            <div className="relative">
                                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
                                <input
                                    type="email"
                                    required
                                    value={email}
                                    onChange={e => setEmail(e.target.value)}
                                    className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-xl pl-10 pr-4 py-3 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-purple-500/50 transition-colors"
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
                                    className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-xl pl-10 pr-4 py-3 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-purple-500/50 transition-colors"
                                    placeholder="••••••••"
                                />
                            </div>
                            <p className="text-xs text-[var(--text-muted)] mt-2 ml-1">Must be at least 6 characters</p>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 mt-6 bg-purple-500 hover:bg-purple-600 disabled:opacity-50 text-white font-medium rounded-xl transition-all shadow-lg shadow-purple-500/20 flex items-center justify-center gap-2"
                        >
                            {loading ? "Creating..." : <>Sign Up <ArrowRight className="w-4 h-4" /></>}
                        </button>
                    </form>

                    <p className="text-center text-sm text-[var(--text-muted)] mt-8">
                        Already have an account? <Link href="/login" className="text-purple-400 hover:text-purple-300 font-medium">Sign in</Link>
                    </p>
                </motion.div>
            </div>
        </div>
    );
}
