"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Plus, Trash2, CheckCircle, ShoppingBag, Upload, FileSpreadsheet, AlertCircle } from "lucide-react";
import { Toaster, toast } from "sonner";
import Link from "next/link";
import { useAuth } from "@/components/AuthProvider";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

interface ImportItem {
    name: string;
    price: string;
    quantity: number;
    unit: string;
    category_id: string;
}

const EMPTY_ITEM: ImportItem = { name: "", price: "", quantity: 1, unit: "piece", category_id: "Grocery" };
const CATEGORIES = ["Grocery", "F&B", "Home & Decor", "Health & Wellness", "Electronics", "Beauty & Personal Care", "Other"];
const UNITS = ["piece", "kg", "g", "litre", "ml", "pack", "dozen", "box"];

export default function ImportPage() {
    const { sellerId, isLoading } = useAuth();
    const activeSellerId = sellerId || "";

    const [tab, setTab] = useState<"manual" | "csv">("manual");
    const [items, setItems] = useState<ImportItem[]>([{ ...EMPTY_ITEM }]);
    const [importing, setImporting] = useState(false);
    const [result, setResult] = useState<{ imported_count: number; total_items: number; errors?: string[] } | null>(null);

    // CSV state
    const [csvFile, setCsvFile] = useState<File | null>(null);
    const [csvPreview, setCsvPreview] = useState<string[][]>([]);
    const [dragging, setDragging] = useState(false);

    const addRow = () => setItems([...items, { ...EMPTY_ITEM }]);

    const updateItem = (idx: number, field: keyof ImportItem, value: string | number) => {
        const updated = [...items];
        updated[idx] = { ...updated[idx], [field]: value };
        setItems(updated);
    };

    const removeRow = (idx: number) => {
        if (items.length === 1) return;
        setItems(items.filter((_, i) => i !== idx));
    };

    const handleManualImport = async () => {
        if (!activeSellerId) return;
        const validItems = items.filter(i => i.name.trim() && i.price.trim());
        if (validItems.length === 0) { toast.error("Fill in at least one item with name and price."); return; }

        setImporting(true);
        const loadingToast = toast.loading(`Adding ${validItems.length} products...`);
        try {
            const res = await fetch(`${API_URL}/api/catalog/import`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
                body: JSON.stringify({ seller_id: activeSellerId, items: validItems }),
            });
            if (res.status === 429) { toast.error("Too many requests. Try again in a bit.", { id: loadingToast }); return; }
            if (res.ok) {
                const data = await res.json();
                setResult(data);
                toast.success(`${data.imported_count} products added to your catalog!`, { id: loadingToast });
            } else {
                toast.error("Something went wrong. Try again.", { id: loadingToast });
            }
        } catch { toast.error("Network error. Check your connection.", { id: loadingToast }); }
        finally { setImporting(false); }
    };

    const parseCSVPreview = (file: File) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const text = e.target?.result as string;
            const lines = text.split("\n").filter(l => l.trim());
            const parsed = lines.slice(0, 6).map(l => {
                const result: string[] = [];
                let current = "";
                let inQuotes = false;
                for (const ch of l) {
                    if (ch === '"') { inQuotes = !inQuotes; }
                    else if (ch === ',' && !inQuotes) { result.push(current.trim()); current = ""; }
                    else { current += ch; }
                }
                result.push(current.trim());
                return result;
            });
            setCsvPreview(parsed);
        };
        reader.readAsText(file);
    };

    const handleFileSelect = (file: File) => {
        if (!file.name.endsWith(".csv")) { toast.error("Please upload a CSV file."); return; }
        setCsvFile(file);
        parseCSVPreview(file);
    };

    const handleCSVImport = async () => {
        if (!activeSellerId || !csvFile) return;
        setImporting(true);
        const loadingToast = toast.loading("Importing CSV...");
        try {
            const formData = new FormData();
            formData.append("file", csvFile);
            formData.append("seller_id", activeSellerId);
            const res = await fetch(`${API_URL}/api/catalog/import/csv`, {
                method: "POST",
                headers: { "X-API-Key": API_KEY },
                body: formData,
            });
            if (res.status === 429) { toast.error("Too many requests.", { id: loadingToast }); return; }
            if (res.ok) {
                const data = await res.json();
                setResult(data);
                toast.success(`${data.imported_count} products imported from CSV!`, { id: loadingToast });
            } else {
                toast.error("CSV import failed.", { id: loadingToast });
            }
        } catch { toast.error("Network error.", { id: loadingToast }); }
        finally { setImporting(false); }
    };

    if (isLoading || !activeSellerId) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500"></div>
            </div>
        );
    }

    return (
        <div className="max-w-3xl mx-auto p-4 md:p-8">
            <Toaster theme="dark" position="top-center" />

            <header className="flex items-center gap-4 py-6 border-b border-[var(--border)] mb-8">
                <Link href="/dashboard" className="flex items-center justify-center w-9 h-9 rounded-lg bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">
                    <ArrowLeft className="w-4 h-4" />
                </Link>
                <motion.h1
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="text-2xl font-extrabold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent"
                >
                    Add Products
                </motion.h1>
            </header>

            {result ? (
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="text-center py-16 bg-[var(--card-bg)] border border-[var(--border)] rounded-2xl"
                >
                    <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-400" />
                    <h2 className="text-xl font-bold text-[var(--text-primary)] mb-2">Products Added!</h2>
                    <p className="text-[var(--text-secondary)] mb-1">{result.imported_count} new products in your catalog</p>
                    <p className="text-sm text-[var(--text-muted)] mb-2">{result.total_items} total items now</p>
                    {result.errors && result.errors.length > 0 && (
                        <div className="mx-8 mt-4 bg-orange-500/5 border border-orange-500/10 rounded-xl p-4 text-left">
                            <p className="text-xs font-semibold text-orange-400 mb-2 flex items-center gap-1.5"><AlertCircle className="w-3.5 h-3.5" /> Some rows had issues:</p>
                            {result.errors.map((e, i) => <p key={i} className="text-xs text-[var(--text-muted)]">{e}</p>)}
                        </div>
                    )}
                    <div className="flex justify-center gap-3 mt-6">
                        <button onClick={() => { setResult(null); setItems([{ ...EMPTY_ITEM }]); setCsvFile(null); setCsvPreview([]); }} className="px-5 py-2 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 rounded-xl text-sm font-semibold hover:bg-cyan-500/20 transition-all">
                            Add More
                        </button>
                        <Link href="/dashboard" className="px-5 py-2 bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text-primary)] rounded-xl text-sm font-semibold hover:bg-[var(--card-hover)] transition-all">
                            Back to Dashboard
                        </Link>
                    </div>
                </motion.div>
            ) : (
                <div className="space-y-6">
                    {/* Tab Switcher */}
                    <div className="flex bg-[var(--card-bg)] border border-[var(--border)] rounded-xl p-1">
                        <button onClick={() => setTab("manual")} className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold transition-all ${tab === "manual" ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20" : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]"}`}>
                            <Plus className="w-4 h-4" /> Manual Entry
                        </button>
                        <button onClick={() => setTab("csv")} className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold transition-all ${tab === "csv" ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20" : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]"}`}>
                            <FileSpreadsheet className="w-4 h-4" /> Upload CSV
                        </button>
                    </div>

                    {tab === "csv" ? (
                        /* CSV Upload Tab */
                        <div className="space-y-4">
                            <div className="flex items-start gap-3 bg-cyan-500/5 border border-cyan-500/10 rounded-xl p-4">
                                <FileSpreadsheet className="w-5 h-5 text-cyan-400 mt-0.5 flex-shrink-0" />
                                <div>
                                    <p className="text-sm font-medium text-[var(--text-primary)]">Upload a CSV file</p>
                                    <p className="text-xs text-[var(--text-muted)] mt-1">Columns: <code className="text-cyan-400">name, price, quantity, unit, category</code></p>
                                </div>
                            </div>

                            {/* Drop zone */}
                            <div
                                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                                onDragLeave={() => setDragging(false)}
                                onDrop={(e) => { e.preventDefault(); setDragging(false); const f = e.dataTransfer.files[0]; if (f) handleFileSelect(f); }}
                                className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all cursor-pointer ${dragging ? "border-cyan-400 bg-cyan-500/5" : "border-[var(--border)] hover:border-cyan-400/50"}`}
                                onClick={() => document.getElementById("csv-input")?.click()}
                            >
                                <input id="csv-input" type="file" accept=".csv" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFileSelect(f); }} />
                                <Upload className={`w-10 h-10 mx-auto mb-3 ${dragging ? "text-cyan-400" : "text-[var(--text-muted)]"}`} />
                                <p className="text-sm font-medium text-[var(--text-primary)]">{csvFile ? csvFile.name : "Drop CSV here or click to browse"}</p>
                                <p className="text-xs text-[var(--text-muted)] mt-1">{csvFile ? `${(csvFile.size / 1024).toFixed(1)} KB` : "Supports .csv files"}</p>
                            </div>

                            {/* Preview */}
                            {csvPreview.length > 0 && (
                                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-[var(--card-bg)] border border-[var(--border)] rounded-xl overflow-hidden">
                                    <div className="px-4 py-3 border-b border-[var(--border)]">
                                        <h3 className="text-sm font-semibold text-[var(--text-primary)]">Preview (first 5 rows)</h3>
                                    </div>
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-xs">
                                            <thead>
                                                <tr className="border-b border-[var(--border)]">
                                                    {csvPreview[0]?.map((h, i) => <th key={i} className="px-3 py-2 text-left text-[var(--text-muted)] font-semibold uppercase tracking-wider">{h}</th>)}
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {csvPreview.slice(1).map((row, i) => (
                                                    <tr key={i} className="border-b border-[var(--border)] last:border-0">
                                                        {row.map((cell, j) => <td key={j} className="px-3 py-2 text-[var(--text-secondary)]">{cell}</td>)}
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </motion.div>
                            )}

                            {csvFile && (
                                <motion.button
                                    initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                                    onClick={handleCSVImport}
                                    disabled={importing}
                                    className="w-full py-3.5 bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-bold rounded-xl shadow-lg hover:shadow-cyan-500/25 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                                >
                                    {importing ? "Importing..." : `Import CSV → Catalog`}
                                </motion.button>
                            )}
                        </div>
                    ) : (
                        /* Manual Entry Tab (existing) */
                        <div className="space-y-6">
                            <div className="flex items-start gap-3 bg-cyan-500/5 border border-cyan-500/10 rounded-xl p-4">
                                <ShoppingBag className="w-5 h-5 text-cyan-400 mt-0.5 flex-shrink-0" />
                                <div>
                                    <p className="text-sm font-medium text-[var(--text-primary)]">Quickly add many products at once</p>
                                    <p className="text-xs text-[var(--text-muted)] mt-1">Fill in your products below — name, price, and quantity. Click "+"  to add more rows.</p>
                                </div>
                            </div>

                            <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-sm font-semibold text-[var(--text-secondary)]">Products ({items.length})</h3>
                                    <button onClick={addRow} className="flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 font-semibold transition-colors">
                                        <Plus className="w-3.5 h-3.5" /> Add Row
                                    </button>
                                </div>

                                <AnimatePresence mode="popLayout">
                                    {items.map((item, idx) => (
                                        <motion.div
                                            key={idx}
                                            layout
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, x: -20 }}
                                            className="bg-[var(--card-bg)] border border-[var(--border)] rounded-xl p-4"
                                        >
                                            <div className="flex items-center gap-2 mb-3">
                                                <span className="text-xs text-[var(--text-muted)] font-mono w-6">#{idx + 1}</span>
                                                {items.length > 1 && (
                                                    <button onClick={() => removeRow(idx)} className="ml-auto p-1.5 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
                                                        <Trash2 className="w-3.5 h-3.5" />
                                                    </button>
                                                )}
                                            </div>
                                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                                                <div className="col-span-2">
                                                    <input
                                                        value={item.name}
                                                        onChange={e => updateItem(idx, "name", e.target.value)}
                                                        placeholder="Product name"
                                                        className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-lg px-3 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
                                                    />
                                                </div>
                                                <div>
                                                    <input
                                                        value={item.price}
                                                        onChange={e => updateItem(idx, "price", e.target.value)}
                                                        placeholder="Price ₹"
                                                        className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-lg px-3 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
                                                    />
                                                </div>
                                                <div>
                                                    <input
                                                        type="number"
                                                        min={0}
                                                        value={item.quantity}
                                                        onChange={e => updateItem(idx, "quantity", parseInt(e.target.value) || 0)}
                                                        placeholder="Qty"
                                                        className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-lg px-3 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
                                                    />
                                                </div>
                                            </div>
                                            <div className="grid grid-cols-2 gap-3 mt-3">
                                                <select
                                                    value={item.unit}
                                                    onChange={e => updateItem(idx, "unit", e.target.value)}
                                                    className="bg-[var(--input-bg)] border border-[var(--input-border)] rounded-lg px-3 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
                                                >
                                                    {UNITS.map(u => <option key={u} value={u}>{u}</option>)}
                                                </select>
                                                <select
                                                    value={item.category_id}
                                                    onChange={e => updateItem(idx, "category_id", e.target.value)}
                                                    className="bg-[var(--input-bg)] border border-[var(--input-border)] rounded-lg px-3 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
                                                >
                                                    {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                                                </select>
                                            </div>
                                        </motion.div>
                                    ))}
                                </AnimatePresence>

                                <button
                                    onClick={addRow}
                                    className="w-full py-3 border-2 border-dashed border-[var(--border)] rounded-xl text-sm font-medium text-[var(--text-muted)] hover:border-cyan-400/50 hover:text-cyan-400 transition-all flex items-center justify-center gap-2"
                                >
                                    <Plus className="w-4 h-4" /> Add another product
                                </button>
                            </div>

                            <motion.button
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                onClick={handleManualImport}
                                disabled={importing}
                                className="w-full py-3.5 bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-bold rounded-xl shadow-lg hover:shadow-cyan-500/25 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {importing ? "Adding..." : `Add ${items.filter(i => i.name.trim()).length} Products to Catalog`}
                            </motion.button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
