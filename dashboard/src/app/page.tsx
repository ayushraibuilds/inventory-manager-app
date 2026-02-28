"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { MessageCircle, ShoppingCart, Globe2, Zap, ArrowRight, ShieldCheck, BarChart3, Users, Store, Package, ArrowLeft } from "lucide-react";
import ThemeToggle from "@/components/ThemeToggle";

// Reusable animation variants
const fadeInUp: any = {
    hidden: { opacity: 0, y: 30 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } }
};

const staggerContainer: any = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: { staggerChildren: 0.15 }
    }
};

export default function LandingPage() {
    return (
        <div className="min-h-screen bg-[var(--bg-primary)] overflow-hidden">
            {/* Navigation */}
            <nav className="fixed top-0 inset-x-0 z-50 bg-[var(--bg-primary)]/80 backdrop-blur-md border-b border-[var(--border)]">
                <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-green-400 to-emerald-600 flex items-center justify-center shadow-lg shadow-green-500/20">
                            <Store className="w-4 h-4 text-white" />
                        </div>
                        <span className="text-xl font-bold bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text text-transparent">
                            Super Seller
                        </span>
                    </div>

                    <div className="flex items-center gap-4">
                        <ThemeToggle />
                        <Link href="/login" className="text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors hidden sm:block">
                            Log in
                        </Link>
                        <Link href="/signup" className="px-5 py-2.5 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-400 hover:to-emerald-500 text-white text-sm font-semibold rounded-full shadow-lg shadow-green-500/25 transition-all hover:scale-105 active:scale-95">
                            Start Free Trial
                        </Link>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 px-6">
                {/* Background glow effects */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-green-500/10 rounded-full blur-[120px] pointer-events-none -z-10" />
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-[100px] pointer-events-none -z-10" />

                <div className="max-w-7xl mx-auto">
                    <div className="text-center max-w-4xl mx-auto">
                        <motion.div
                            initial="hidden"
                            animate="visible"
                            variants={staggerContainer}
                            className="space-y-8"
                        >
                            <motion.div variants={fadeInUp} className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-green-500/10 border border-green-500/20 text-green-500 text-sm font-medium mb-4">
                                <span className="relative flex h-2 w-2">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                                </span>
                                Now live on the ONDC Network
                            </motion.div>

                            <motion.h1 variants={fadeInUp} className="text-5xl lg:text-7xl font-extrabold text-[var(--text-primary)] tracking-tight leading-[1.1]">
                                Sell on ONDC via <br />
                                <span className="inline-block relative">
                                    <span className="relative z-10 bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text text-transparent">WhatsApp.</span>
                                    <svg className="absolute w-full h-4 -bottom-1 left-0 -z-10 text-green-500/40" viewBox="0 0 100 10" preserveAspectRatio="none">
                                        <path d="M0 5 Q 50 10 100 5" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
                                    </svg>
                                </span>
                            </motion.h1>

                            <motion.p variants={fadeInUp} className="text-xl text-[var(--text-secondary)] leading-relaxed max-w-2xl mx-auto">
                                No complex apps or portals. Manage your entire catalog, process orders, and reach millions of buyers on the ONDC network — all from the comfort of WhatsApp.
                            </motion.p>

                            <motion.div variants={fadeInUp} className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
                                <Link href="/signup" className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-400 hover:to-emerald-500 text-white font-bold rounded-xl shadow-xl shadow-green-500/25 transition-all hover:-translate-y-1 flex items-center justify-center gap-2 text-lg">
                                    Get Started for Free <ArrowRight className="w-5 h-5" />
                                </Link>
                                <Link href="#how-it-works" className="w-full sm:w-auto px-8 py-4 bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text-primary)] font-bold rounded-xl shadow-sm hover:bg-[var(--card-hover)] transition-all flex items-center justify-center gap-2 text-lg">
                                    See how it works
                                </Link>
                            </motion.div>

                            <motion.p variants={fadeInUp} className="text-sm text-[var(--text-muted)] pt-4">
                                No credit card required • 14-day free trial • Set up in 2 minutes
                            </motion.p>
                        </motion.div>
                    </div>

                    {/* Dashboard Preview / Mockup */}
                    <motion.div
                        initial={{ opacity: 0, y: 50 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.5, duration: 0.8 }}
                        className="mt-20 relative mx-auto w-full max-w-5xl rounded-2xl md:rounded-[2rem] border border-[var(--border)] bg-[#0A0A0B] shadow-2xl overflow-hidden shadow-green-500/10"
                    >
                        {/* Fake Browser Chrome */}
                        <div className="h-10 border-b border-white/10 bg-white/5 flex items-center px-4 gap-2">
                            <div className="flex gap-1.5">
                                <div className="w-3 h-3 rounded-full bg-red-500/80" />
                                <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                                <div className="w-3 h-3 rounded-full bg-green-500/80" />
                            </div>
                            <div className="mx-auto px-3 py-1 bg-white/5 rounded-md flex items-center gap-2 text-xs text-white/40 max-w-[200px] w-full justify-center">
                                <ShieldCheck className="w-3 h-3" />
                                app.superseller.in
                            </div>
                        </div>

                        {/* The "screenshot" inside */}
                        <div className="p-4 md:p-8 bg-[url('https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=2000&q=80')] bg-cover bg-center h-[300px] md:h-[500px] relative">
                            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

                            {/* Fake Dashboard Elements */}
                            <div className="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-6 h-full">
                                <div className="col-span-2 space-y-6">
                                    {/* Fake Header */}
                                    <div className="flex justify-between items-center">
                                        <h3 className="text-2xl font-bold text-white">Dashboard</h3>
                                        <div className="h-8 w-24 bg-white/10 rounded-full" />
                                    </div>
                                    {/* Fake stats */}
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="h-24 bg-white/10 rounded-xl border border-white/5 p-4 flex flex-col justify-between backdrop-blur-md">
                                            <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center"><Package className="text-blue-400 w-4 h-4" /></div>
                                            <div className="h-6 w-16 bg-white/20 rounded-md" />
                                        </div>
                                        <div className="h-24 bg-white/10 rounded-xl border border-white/5 p-4 flex flex-col justify-between backdrop-blur-md">
                                            <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center"><BarChart3 className="text-green-400 w-4 h-4" /></div>
                                            <div className="h-6 w-24 bg-white/20 rounded-md" />
                                        </div>
                                    </div>
                                    {/* Fake Table */}
                                    <div className="flex-1 bg-white/10 rounded-xl border border-white/5 p-4 backdrop-blur-md hidden md:block">
                                        <div className="h-8 border-b border-white/10 flex items-center gap-4 mb-4">
                                            <div className="h-4 w-32 bg-white/20 rounded" />
                                            <div className="h-4 w-16 bg-white/20 rounded" />
                                        </div>
                                        <div className="space-y-3">
                                            {[1, 2, 3].map(i => (
                                                <div key={i} className="h-6 flex items-center gap-4">
                                                    <div className="h-4 w-8 bg-white/10 rounded" />
                                                    <div className="h-4 w-full bg-white/10 rounded" />
                                                    <div className="h-4 w-16 bg-white/10 rounded" />
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                {/* Fake Mobile Phone / WhatsApp Mockup */}
                                <div className="hidden md:flex flex-col items-center justify-center relative translate-y-12">
                                    <div className="w-[240px] h-[480px] bg-black rounded-[2.5rem] border-4 border-[#333] shadow-2xl relative overflow-hidden flex flex-col">
                                        <div className="h-14 bg-[#075E54] flex items-center px-4 gap-3 text-white">
                                            <ArrowLeft className="w-5 h-5" />
                                            <div className="flex-1">
                                                <h4 className="font-semibold text-sm">Super Seller Bot</h4>
                                                <p className="text-[10px] text-white/70">online</p>
                                            </div>
                                        </div>
                                        <div className="flex-1 bg-[#ECE5DD] p-4 flex flex-col gap-3">
                                            <div className="bg-white p-2 rounded-xl rounded-tl-none self-start max-w-[85%] text-sm shadow-sm">
                                                <p className="font-semibold text-green-600 mb-1 text-xs">New Order #892</p>
                                                <p className="text-gray-800 text-xs">Item: Aashirvaad Atta 5kg</p>
                                                <p className="text-gray-800 text-xs">Total: ₹240</p>
                                                <div className="flex gap-2 mt-2">
                                                    <span className="bg-green-100 text-green-700 px-2 py-1 rounded text-[10px] font-medium border border-green-200 cursor-pointer">Accept</span>
                                                    <span className="bg-red-100 text-red-700 px-2 py-1 rounded text-[10px] font-medium border border-red-200 cursor-pointer">Reject</span>
                                                </div>
                                            </div>
                                            <div className="bg-[#DCF8C6] p-2 rounded-xl rounded-tr-none self-end text-sm shadow-sm">
                                                <p className="text-gray-800 text-xs">Accept</p>
                                            </div>
                                            <div className="bg-white p-2 rounded-xl rounded-tl-none self-start max-w-[85%] text-sm shadow-sm">
                                                <p className="text-gray-800 text-xs">Order Accepted! Notified buyer on ONDC.</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* How it works */}
            <section id="how-it-works" className="py-24 bg-[var(--card-bg)] border-y border-[var(--border)]">
                <div className="max-w-7xl mx-auto px-6">
                    <div className="text-center max-w-3xl mx-auto mb-16">
                        <h2 className="text-3xl lg:text-4xl font-bold text-[var(--text-primary)] mb-4">Simple, fast, and familiar.</h2>
                        <p className="text-lg text-[var(--text-secondary)]">Join the ONDC network without learning new software. If you know how to chat on WhatsApp, you know how to sell.</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <div className="bg-[var(--bg-primary)] p-8 rounded-3xl border border-[var(--border)] relative overflow-hidden group hover:border-green-500/50 transition-colors">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-green-500/10 rounded-bl-full -z-10 transition-transform group-hover:scale-110" />
                            <div className="w-14 h-14 rounded-2xl bg-green-500/10 border border-green-500/20 flex items-center justify-center mb-6">
                                <MessageCircle className="w-7 h-7 text-green-500" />
                            </div>
                            <h3 className="text-xl font-bold text-[var(--text-primary)] mb-3">1. Connect WhatsApp</h3>
                            <p className="text-[var(--text-secondary)] leading-relaxed">Simply message our verified WhatsApp bot to create your seller account instantly.</p>
                        </div>

                        <div className="bg-[var(--bg-primary)] p-8 rounded-3xl border border-[var(--border)] relative overflow-hidden group hover:border-blue-500/50 transition-colors">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-bl-full -z-10 transition-transform group-hover:scale-110" />
                            <div className="w-14 h-14 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-6">
                                <Globe2 className="w-7 h-7 text-blue-500" />
                            </div>
                            <h3 className="text-xl font-bold text-[var(--text-primary)] mb-3">2. Add Products</h3>
                            <p className="text-[var(--text-secondary)] leading-relaxed">Send a photo of your product or type its name. The AI auto-creates the catalog listing.</p>
                        </div>

                        <div className="bg-[var(--bg-primary)] p-8 rounded-3xl border border-[var(--border)] relative overflow-hidden group hover:border-purple-500/50 transition-colors">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/10 rounded-bl-full -z-10 transition-transform group-hover:scale-110" />
                            <div className="w-14 h-14 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mb-6">
                                <ShoppingCart className="w-7 h-7 text-purple-500" />
                            </div>
                            <h3 className="text-xl font-bold text-[var(--text-primary)] mb-3">3. Receive Orders</h3>
                            <p className="text-[var(--text-secondary)] leading-relaxed">Get instantly notified on WhatsApp when a buyer orders from any ONDC buyer app.</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Grid */}
            <section className="py-24 px-6">
                <div className="max-w-7xl mx-auto">
                    <div className="flex flex-col md:flex-row items-end justify-between mb-16 gap-6">
                        <div className="max-w-2xl">
                            <h2 className="text-3xl lg:text-4xl font-bold text-[var(--text-primary)] mb-4">Everything you need to scale</h2>
                            <p className="text-lg text-[var(--text-secondary)]">While WhatsApp handles the day-to-day, our powerful web dashboard gives you full control over your business.</p>
                        </div>
                        <Link href="/signup" className="px-6 py-3 bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text-primary)] font-semibold rounded-xl hover:bg-[var(--card-hover)] transition-all flex items-center gap-2">
                            Explore Dashboard <ArrowRight className="w-4 h-4" />
                        </Link>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[
                            { icon: BarChart3, title: "Real-time Analytics", desc: "Track your sales, inventory value, and top performing products instantly.", color: "text-blue-500", bg: "bg-blue-500/10", border: "border-blue-500/20" },
                            { icon: Zap, title: "Low Stock Alerts", desc: "Get automated WhatsApp alerts before your bestsellers run out.", color: "text-amber-500", bg: "bg-amber-500/10", border: "border-amber-500/20" },
                            { icon: Users, title: "Multilingual Support", desc: "Chat in English, Hindi, Tamil, or 12 other supported Indian languages.", color: "text-purple-500", bg: "bg-purple-500/10", border: "border-purple-500/20" },
                        ].map((f, i) => (
                            <div key={i} className="p-6 rounded-2xl bg-[var(--card-bg)] border border-[var(--border)] hover:shadow-xl transition-all">
                                <div className={`w-12 h-12 rounded-xl ${f.bg} ${f.border} border flex items-center justify-center mb-5`}>
                                    <f.icon className={`w-6 h-6 ${f.color}`} />
                                </div>
                                <h4 className="text-lg font-bold text-[var(--text-primary)] mb-2">{f.title}</h4>
                                <p className="text-[var(--text-secondary)]">{f.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-32 px-6 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-b from-transparent to-green-500/5 pointer-events-none" />
                <div className="max-w-4xl mx-auto text-center relative z-10">
                    <h2 className="text-4xl lg:text-6xl font-extrabold text-[var(--text-primary)] mb-6 tracking-tight">
                        Ready to join the revolution?
                    </h2>
                    <p className="text-xl text-[var(--text-secondary)] mb-10 max-w-2xl mx-auto">
                        Join thousands of small businesses leveraging ONDC to reach more customers, without high commissions.
                    </p>
                    <Link href="/signup" className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-bold rounded-xl shadow-2xl shadow-green-500/25 hover:scale-105 transition-all text-lg">
                        Create your store now <ArrowRight className="w-5 h-5" />
                    </Link>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-12 border-t border-[var(--border)] bg-[var(--bg-primary)]">
                <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
                    <div className="flex items-center gap-2">
                        <Store className="w-5 h-5 text-green-500" />
                        <span className="font-bold text-[var(--text-primary)]">Super Seller</span>
                    </div>
                    <p className="text-[var(--text-secondary)] text-sm">
                        © {new Date().getFullYear()} ONDC Super Seller Demo. Built for showcasing.
                    </p>
                    <div className="flex gap-4">
                        <Link href="#" className="text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">Privacy</Link>
                        <Link href="#" className="text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">Terms</Link>
                    </div>
                </div>
            </footer>
        </div>
    );
}
