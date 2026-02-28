"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Save, Store, MapPin, FileText, Phone, Image, Bell } from "lucide-react";
import { Toaster, toast } from "sonner";
import Link from "next/link";
import { useAuth } from "@/components/AuthProvider";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

interface SellerProfile {
    seller_id: string;
    store_name: string;
    address: string;
    gst_number: string;
    logo_url: string;
    phone: string;
    low_stock_alerts: boolean;
    updated_at: string | null;
}

export default function SellerProfilePage({ params }: { params: Promise<{ id: string }> }) {
    const { sellerId: authSellerId, isLoading: authLoading } = useAuth();
    const activeSellerId = authSellerId || "";

    const [sellerId, setSellerId] = useState<string>("");
    const [profile, setProfile] = useState<SellerProfile | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    const [form, setForm] = useState({
        store_name: "",
        address: "",
        gst_number: "",
        logo_url: "",
        phone: "",
        low_stock_alerts: false,
    });

    useEffect(() => {
        if (!authLoading && activeSellerId) {
            setSellerId(activeSellerId); // keeping local state for display purposes
            fetchProfile(activeSellerId);
        }
    }, [authLoading, activeSellerId]);

    const fetchProfile = async (id: string) => {
        try {
            const res = await fetch(`${API_URL}/api/seller/${encodeURIComponent(id)}/profile`);
            if (res.status === 429) {
                toast.error("Rate limit exceeded. Please try again later.");
                return;
            }
            if (res.ok) {
                const data = await res.json();
                setProfile(data.profile);
                setForm({
                    store_name: data.profile.store_name || "",
                    address: data.profile.address || "",
                    gst_number: data.profile.gst_number || "",
                    logo_url: data.profile.logo_url || "",
                    phone: data.profile.phone || "",
                    low_stock_alerts: !!data.profile.low_stock_alerts,
                });
            }
        } catch {
            toast.error("Failed to load profile");
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        try {
            const res = await fetch(`${API_URL}/api/seller/${encodeURIComponent(sellerId)}/profile`, {
                method: "PUT",
                headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
                body: JSON.stringify(form),
            });
            if (res.status === 429) {
                toast.error("Rate limit exceeded. Please try again later.");
                return;
            }
            if (res.ok) {
                const data = await res.json();
                setProfile(data.profile);
                toast.success("Profile saved!");
            } else {
                toast.error("Failed to save profile");
            }
        } catch {
            toast.error("Network error");
        } finally {
            setSaving(false);
        }
    };

    const formatSellerId = (id: string) => {
        if (id.startsWith("whatsapp:+")) return id.replace("whatsapp:", "");
        return id;
    };

    const [isMounted, setIsMounted] = useState(false);
    useEffect(() => { setIsMounted(true); }, []);

    if (!isMounted || loading || authLoading || !activeSellerId) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
            </div>
        );
    }

    return (
        <div className="max-w-3xl mx-auto p-4 md:p-8">
            <Toaster theme="dark" position="top-center" />

            <header className="flex items-center gap-4 py-6 border-b border-[var(--border)] mb-8">
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
                    className="text-2xl font-extrabold bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent tracking-tight"
                >
                    Seller Profile
                </motion.h1>
            </header>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-[var(--card-bg)] backdrop-blur-xl border border-[var(--border)] rounded-2xl p-6 md:p-8 shadow-2xl"
            >
                <div className="flex items-center gap-3 mb-6 pb-4 border-b border-[var(--border)]">
                    <div className="w-10 h-10 rounded-full bg-green-500/10 border border-green-500/20 flex items-center justify-center">
                        <Store className="w-5 h-5 text-green-400" />
                    </div>
                    <div>
                        <p className="text-sm font-semibold text-[var(--text-primary)]">{formatSellerId(sellerId)}</p>
                        {profile?.updated_at && (
                            <p className="text-xs text-[var(--text-muted)]">
                                Last updated: {new Date(profile.updated_at + "Z").toLocaleDateString()}
                            </p>
                        )}
                    </div>
                </div>

                <form onSubmit={handleSave} className="space-y-5">
                    <div>
                        <label className="flex items-center gap-2 text-sm font-medium text-[var(--text-secondary)] mb-1.5">
                            <Store className="w-3.5 h-3.5" /> Store Name
                        </label>
                        <input
                            value={form.store_name}
                            onChange={e => setForm({ ...form, store_name: e.target.value })}
                            className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-lg px-4 py-2.5 text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500 transition-all placeholder-[var(--text-muted)]"
                            placeholder="e.g. Ram's Kirana Store"
                        />
                    </div>

                    <div>
                        <label className="flex items-center gap-2 text-sm font-medium text-[var(--text-secondary)] mb-1.5">
                            <MapPin className="w-3.5 h-3.5" /> Address
                        </label>
                        <textarea
                            value={form.address}
                            onChange={e => setForm({ ...form, address: e.target.value })}
                            rows={2}
                            className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-lg px-4 py-2.5 text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500 transition-all placeholder-[var(--text-muted)] resize-none"
                            placeholder="e.g. Shop #12, MG Road, Pune 411001"
                        />
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <label className="flex items-center gap-2 text-sm font-medium text-[var(--text-secondary)] mb-1.5">
                                <FileText className="w-3.5 h-3.5" /> GST Number
                            </label>
                            <input
                                value={form.gst_number}
                                onChange={e => setForm({ ...form, gst_number: e.target.value })}
                                className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-lg px-4 py-2.5 text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500 transition-all placeholder-[var(--text-muted)]"
                                placeholder="e.g. 27AABCU9603R1ZM"
                            />
                        </div>
                        <div>
                            <label className="flex items-center gap-2 text-sm font-medium text-[var(--text-secondary)] mb-1.5">
                                <Phone className="w-3.5 h-3.5" /> Phone
                            </label>
                            <input
                                value={form.phone}
                                onChange={e => setForm({ ...form, phone: e.target.value })}
                                className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-lg px-4 py-2.5 text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500 transition-all placeholder-[var(--text-muted)]"
                                placeholder="e.g. +91 93404 99553"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="flex items-center gap-2 text-sm font-medium text-[var(--text-secondary)] mb-1.5">
                            <Image className="w-3.5 h-3.5" /> Logo URL
                        </label>
                        <input
                            value={form.logo_url}
                            onChange={e => setForm({ ...form, logo_url: e.target.value })}
                            className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-lg px-4 py-2.5 text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500 transition-all placeholder-[var(--text-muted)]"
                            placeholder="https://example.com/logo.png"
                        />
                    </div>

                    {/* Low Stock Alerts Toggle */}
                    <div className="pt-4 border-t border-[var(--border)]">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className={`w-9 h-9 rounded-full flex items-center justify-center ${form.low_stock_alerts ? 'bg-amber-500/10 border border-amber-500/20' : 'bg-[var(--card-bg)] border border-[var(--border)]'}`}>
                                    <Bell className={`w-4 h-4 ${form.low_stock_alerts ? 'text-amber-400' : 'text-[var(--text-muted)]'}`} />
                                </div>
                                <div>
                                    <p className="text-sm font-medium text-[var(--text-primary)]">Low Stock WhatsApp Alerts</p>
                                    <p className="text-xs text-[var(--text-muted)]">Get notified when items drop below 5 units</p>
                                </div>
                            </div>
                            <button
                                type="button"
                                onClick={() => setForm({ ...form, low_stock_alerts: !form.low_stock_alerts })}
                                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-green-500/50 ${form.low_stock_alerts ? 'bg-green-500' : 'bg-[var(--input-bg)] border border-[var(--input-border)]'}`}
                            >
                                <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform duration-200 ${form.low_stock_alerts ? 'translate-x-6' : 'translate-x-1'}`} />
                            </button>
                        </div>
                    </div>

                    <div className="pt-4 border-t border-[var(--border)]">
                        <button
                            type="submit"
                            disabled={saving}
                            className="flex items-center gap-2 bg-green-500 hover:bg-green-600 disabled:opacity-50 text-white font-medium px-6 py-2.5 rounded-lg transition-all active:scale-95 shadow-lg shadow-green-500/20"
                        >
                            <Save className="w-4 h-4" />
                            {saving ? "Saving..." : "Save Profile"}
                        </button>
                    </div>
                </form>
            </motion.div>
        </div>
    );
}
