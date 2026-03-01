"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Store, Package, PartyPopper, ArrowRight, ArrowLeft, Check, Sparkles } from "lucide-react";
import { Toaster, toast } from "sonner";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

const STEPS = [
    { icon: Store, title: "Your Store", subtitle: "Tell us about your business" },
    { icon: Package, title: "First Product", subtitle: "Add your first item to sell" },
    { icon: PartyPopper, title: "Ready!", subtitle: "You're all set to sell on ONDC" },
];

export default function OnboardingPage() {
    const { sellerId, token, isLoading } = useAuth();
    const router = useRouter();
    const activeSellerId = sellerId || "";

    const [step, setStep] = useState(0);
    const [saving, setSaving] = useState(false);

    // Step 1 state
    const [storeName, setStoreName] = useState("");
    const [address, setAddress] = useState("");
    const [gst, setGst] = useState("");

    // Step 2 state
    const [productName, setProductName] = useState("");
    const [productPrice, setProductPrice] = useState("");
    const [productQty, setProductQty] = useState("10");
    const [productUnit, setProductUnit] = useState("piece");

    const saveProfile = async () => {
        if (!storeName.trim()) { toast.error("Store name is required."); return; }
        setSaving(true);
        try {
            const res = await fetch(`${API_URL}/api/seller/${encodeURIComponent(activeSellerId)}/profile`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-Key": API_KEY,
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ store_name: storeName.trim(), address: address.trim(), gst_number: gst.trim() }),
            });
            if (res.ok) {
                toast.success("Store profile saved!");
                setStep(1);
            } else { toast.error("Failed to save profile."); }
        } catch { toast.error("Network error."); }
        finally { setSaving(false); }
    };

    const addFirstProduct = async () => {
        if (!productName.trim() || !productPrice.trim()) { toast.error("Product name and price are required."); return; }
        setSaving(true);
        try {
            const res = await fetch(`${API_URL}/api/catalog/item`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-Key": API_KEY,
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    seller_id: activeSellerId,
                    name: productName.trim(),
                    price: productPrice.trim(),
                    quantity: parseInt(productQty) || 1,
                    unit: productUnit,
                    category_id: "Grocery",
                }),
            });
            if (res.ok) {
                const data = await res.json();
                toast.success(data.message || "Product added!");
                setStep(2);
            } else { toast.error("Failed to add product."); }
        } catch { toast.error("Network error."); }
        finally { setSaving(false); }
    };

    const skipProduct = () => setStep(2);

    if (isLoading || !activeSellerId) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center p-4">
            <Toaster theme="dark" position="top-center" />

            <div className="w-full max-w-md">
                {/* Progress bar */}
                <div className="flex items-center gap-2 mb-8">
                    {STEPS.map((s, i) => (
                        <div key={i} className="flex items-center flex-1 gap-2">
                            <div
                                className={`flex items-center justify-center w-8 h-8 rounded-full border-2 transition-all ${i < step ? "bg-green-500 border-green-500 text-white" :
                                    i === step ? "border-cyan-400 text-cyan-400" :
                                        "border-[var(--border)] text-[var(--text-muted)]"
                                    }`}
                            >
                                {i < step ? <Check className="w-4 h-4" /> : <s.icon className="w-4 h-4" />}
                            </div>
                            {i < STEPS.length - 1 && (
                                <div className={`flex-1 h-0.5 transition-all ${i < step ? "bg-green-500" : "bg-[var(--border)]"}`} />
                            )}
                        </div>
                    ))}
                </div>

                <AnimatePresence mode="wait">
                    {step === 0 && (
                        <motion.div
                            key="step-0"
                            initial={{ opacity: 0, x: 30 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -30 }}
                            className="bg-[var(--card-bg)] border border-[var(--border)] rounded-2xl p-6 shadow-xl"
                        >
                            <Store className="w-10 h-10 text-cyan-400 mb-4" />
                            <h2 className="text-xl font-bold text-[var(--text-primary)] mb-1">Set up your store</h2>
                            <p className="text-sm text-[var(--text-muted)] mb-6">This info will be visible to buyers on the ONDC network.</p>

                            <div className="space-y-4">
                                <div>
                                    <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1.5 block">Store Name *</label>
                                    <input
                                        value={storeName}
                                        onChange={e => setStoreName(e.target.value)}
                                        placeholder="e.g., Ramesh General Store"
                                        className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-xl px-4 py-3 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
                                    />
                                </div>
                                <div>
                                    <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1.5 block">Address</label>
                                    <input
                                        value={address}
                                        onChange={e => setAddress(e.target.value)}
                                        placeholder="e.g., 42 MG Road, Pune"
                                        className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-xl px-4 py-3 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
                                    />
                                </div>
                                <div>
                                    <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1.5 block">GST Number <span className="text-[var(--text-muted)] font-normal">(optional)</span></label>
                                    <input
                                        value={gst}
                                        onChange={e => setGst(e.target.value)}
                                        placeholder="22AAAAA0000A1Z5"
                                        className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-xl px-4 py-3 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
                                    />
                                </div>
                            </div>

                            <button
                                onClick={saveProfile}
                                disabled={saving}
                                className="w-full mt-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-bold rounded-xl shadow-lg hover:shadow-cyan-500/25 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {saving ? "Saving..." : <>Continue <ArrowRight className="w-4 h-4" /></>}
                            </button>
                        </motion.div>
                    )}

                    {step === 1 && (
                        <motion.div
                            key="step-1"
                            initial={{ opacity: 0, x: 30 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -30 }}
                            className="bg-[var(--card-bg)] border border-[var(--border)] rounded-2xl p-6 shadow-xl"
                        >
                            <Package className="w-10 h-10 text-green-400 mb-4" />
                            <h2 className="text-xl font-bold text-[var(--text-primary)] mb-1">Add your first product</h2>
                            <p className="text-sm text-[var(--text-muted)] mb-6">This will be your first listing on the ONDC network.</p>

                            <div className="space-y-4">
                                <div>
                                    <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1.5 block">Product Name *</label>
                                    <input
                                        value={productName}
                                        onChange={e => setProductName(e.target.value)}
                                        placeholder="e.g., Aashirvaad Atta 5kg"
                                        className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-xl px-4 py-3 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-green-500/30"
                                    />
                                </div>
                                <div className="grid grid-cols-3 gap-3">
                                    <div>
                                        <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1.5 block">Price (₹) *</label>
                                        <input
                                            value={productPrice}
                                            onChange={e => setProductPrice(e.target.value)}
                                            placeholder="240"
                                            className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-xl px-4 py-3 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-green-500/30"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1.5 block">Quantity</label>
                                        <input
                                            type="number"
                                            min={1}
                                            value={productQty}
                                            onChange={e => setProductQty(e.target.value)}
                                            className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-xl px-4 py-3 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-green-500/30"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1.5 block">Unit</label>
                                        <select
                                            value={productUnit}
                                            onChange={e => setProductUnit(e.target.value)}
                                            className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-xl px-4 py-3 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-green-500/30"
                                        >
                                            {["piece", "kg", "g", "litre", "ml", "pack"].map(u => <option key={u} value={u}>{u}</option>)}
                                        </select>
                                    </div>
                                </div>
                            </div>

                            <div className="flex gap-3 mt-6">
                                <button
                                    onClick={() => setStep(0)}
                                    className="px-5 py-3 bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text-secondary)] rounded-xl text-sm font-semibold hover:bg-[var(--card-hover)] transition-all"
                                >
                                    <ArrowLeft className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={skipProduct}
                                    className="flex-1 py-3 bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text-secondary)] rounded-xl text-sm font-semibold hover:bg-[var(--card-hover)] transition-all"
                                >
                                    Skip
                                </button>
                                <button
                                    onClick={addFirstProduct}
                                    disabled={saving}
                                    className="flex-1 py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-bold rounded-xl shadow-lg hover:shadow-green-500/25 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                                >
                                    {saving ? "Adding..." : <>Add Product <ArrowRight className="w-4 h-4" /></>}
                                </button>
                            </div>
                        </motion.div>
                    )}

                    {step === 2 && (
                        <motion.div
                            key="step-2"
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="bg-[var(--card-bg)] border border-[var(--border)] rounded-2xl p-8 shadow-xl text-center"
                        >
                            <motion.div
                                initial={{ rotate: -20, scale: 0 }}
                                animate={{ rotate: 0, scale: 1 }}
                                transition={{ type: "spring", delay: 0.2 }}
                            >
                                <Sparkles className="w-16 h-16 mx-auto mb-4 text-yellow-400" />
                            </motion.div>
                            <h2 className="text-2xl font-extrabold text-[var(--text-primary)] mb-2">You&apos;re live on ONDC! 🎉</h2>
                            <p className="text-sm text-[var(--text-muted)] mb-8">Your store is now discoverable by millions of buyers across India.</p>

                            <div className="space-y-3">
                                <button
                                    onClick={() => router.push("/dashboard")}
                                    className="w-full py-3.5 bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-bold rounded-xl shadow-lg hover:shadow-cyan-500/25 transition-all flex items-center justify-center gap-2"
                                >
                                    Go to Dashboard <ArrowRight className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={() => router.push("/import")}
                                    className="w-full py-3 bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text-secondary)] rounded-xl text-sm font-semibold hover:bg-[var(--card-hover)] transition-all"
                                >
                                    Add more products
                                </button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
