import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PackageSearch, Plus, RefreshCw, Edit2, Trash2, CheckSquare, Square, Download } from "lucide-react";

export interface CatalogItem {
    id: string;
    name: string;
    price: string;
    quantity: number;
    unit: string;
    category_id: string;
}

interface InventoryTableProps {
    items: CatalogItem[];
    loading: boolean;
    isRefreshing: boolean;
    currentPage: number;
    totalPages: number;
    onPageChange: (page: number) => void;
    onRefresh: () => void;
    onAddClick: () => void;
    onEditClick: (item: CatalogItem) => void;
    onDeleteClick: (item: CatalogItem) => void;
    onBulkDelete: (items: CatalogItem[]) => void;
}

export default function InventoryTable({
    items,
    loading,
    isRefreshing,
    currentPage,
    totalPages,
    onPageChange,
    onRefresh,
    onAddClick,
    onEditClick,
    onDeleteClick,
    onBulkDelete
}: InventoryTableProps) {
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

    // Keyboard Shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            const isInput = e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement;

            // Ctrl/Cmd + K
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                document.getElementById('search-catalog-input')?.focus();
            }

            // Delete or Backspace
            if ((e.key === 'Delete' || e.key === 'Backspace') && !isInput && selectedIds.size > 0) {
                e.preventDefault();
                const selected = items.filter(i => selectedIds.has(i.id));
                onBulkDelete(selected);
                setSelectedIds(new Set());
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [selectedIds, items, onBulkDelete]);

    const filteredItems = items.filter(item =>
        item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.id.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const allSelected = filteredItems.length > 0 && filteredItems.every(item => selectedIds.has(item.id));

    const toggleSelectAll = () => {
        if (allSelected) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(filteredItems.map(item => item.id)));
        }
    };

    const toggleSelect = (id: string) => {
        const next = new Set(selectedIds);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        setSelectedIds(next);
    };

    const handleBulkDelete = () => {
        const selected = items.filter(i => selectedIds.has(i.id));
        onBulkDelete(selected);
        setSelectedIds(new Set());
    };

    const exportCsv = () => {
        const header = "ID,Name,Price (INR),Quantity,Unit,Category\n";
        const rows = filteredItems.map(i =>
            `"${i.id}","${i.name}","${i.price}","${i.quantity}","${i.unit}","${i.category_id}"`
        ).join("\n");
        const blob = new Blob([header + rows], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `ondc-catalog-${new Date().toISOString().split("T")[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-[var(--card-bg)] backdrop-blur-xl border border-[var(--border)] rounded-2xl p-6 shadow-2xl"
        >
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
                <h2 className="text-xl font-bold text-[var(--text-primary)] flex items-center gap-2">
                    <PackageSearch className="w-5 h-5 text-primary" />
                    Live Inventory
                </h2>

                <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
                    <input
                        id="search-catalog-input"
                        type="text"
                        placeholder="Search items (Ctrl+K)..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="bg-[var(--input-bg)] border border-[var(--input-border)] rounded-lg px-4 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all w-full sm:w-48 placeholder-[var(--text-muted)]"
                    />
                    <div className="flex gap-2">
                        <button
                            onClick={onAddClick}
                            className="flex items-center gap-1.5 bg-primary hover:bg-blue-500 text-white px-3.5 py-2 rounded-lg font-medium transition-all shadow-lg hover:shadow-primary/20 active:scale-95 text-sm"
                        >
                            <Plus className="w-4 h-4" /> Add
                        </button>
                        <button
                            onClick={exportCsv}
                            className="flex items-center gap-1.5 bg-[var(--card-bg)] hover:bg-[var(--card-hover)] border border-[var(--border)] text-[var(--text-primary)] px-3.5 py-2 rounded-lg font-medium transition-all active:scale-95 text-sm"
                            title="Export CSV"
                        >
                            <Download className="w-4 h-4" />
                        </button>
                        <button
                            onClick={onRefresh}
                            className="flex items-center gap-1.5 bg-[var(--card-bg)] hover:bg-[var(--card-hover)] border border-[var(--border)] text-[var(--text-primary)] px-3.5 py-2 rounded-lg font-medium transition-all active:scale-95 text-sm"
                        >
                            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-primary' : ''}`} />
                        </button>
                    </div>
                </div>
            </div>

            {/* Bulk action bar */}
            <AnimatePresence>
                {selectedIds.size > 0 && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mb-4 overflow-hidden"
                    >
                        <div className="flex items-center gap-3 bg-primary/5 border border-primary/20 rounded-xl px-4 py-2.5 text-sm">
                            <span className="text-primary font-semibold">{selectedIds.size} selected</span>
                            <div className="flex-1" />
                            <button
                                onClick={handleBulkDelete}
                                className="flex items-center gap-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors border border-red-500/20"
                            >
                                <Trash2 className="w-3.5 h-3.5" /> Delete Selected
                            </button>
                            <button
                                onClick={() => setSelectedIds(new Set())}
                                className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-xs font-medium px-2 py-1.5 transition-colors"
                            >
                                Clear
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {loading && items.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-[var(--text-muted)]">
                    <RefreshCw className="w-8 h-8 animate-spin mb-4 text-primary" />
                    <p>Syncing with ONDC Network...</p>
                </div>
            ) : items.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-center border border-dashed border-[var(--border)] rounded-xl bg-[var(--card-bg)]">
                    <span className="text-5xl mb-4">📱</span>
                    <p className="text-lg font-medium text-[var(--text-primary)] mb-2">Waiting for WhatsApp listings...</p>
                    <p className="text-sm text-[var(--text-secondary)] max-w-sm">
                        Send a message to the bot or add a product directly to see inventory appear here.
                    </p>
                </div>
            ) : filteredItems.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-10 text-[var(--text-muted)]">
                    <p>No products match your search.</p>
                </div>
            ) : (
                <div className="overflow-x-auto rounded-xl border border-[var(--border)] bg-[var(--bg-primary)]">
                    <table className="w-full text-left text-sm whitespace-nowrap">
                        <thead className="bg-[var(--card-bg)] text-[var(--text-secondary)] font-semibold uppercase tracking-wider text-xs">
                            <tr>
                                <th className="px-4 py-4 w-10">
                                    <button onClick={toggleSelectAll} className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">
                                        {allSelected ? <CheckSquare className="w-4 h-4 text-primary" /> : <Square className="w-4 h-4" />}
                                    </button>
                                </th>
                                <th className="px-4 py-4">Item ID</th>
                                <th className="px-4 py-4">Product Name</th>
                                <th className="px-4 py-4">Price</th>
                                <th className="px-4 py-4">Available Qty</th>
                                <th className="px-4 py-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-[var(--border)]">
                            <AnimatePresence mode="popLayout">
                                {filteredItems.map((item) => (
                                    <motion.tr
                                        key={item.id}
                                        layout
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, x: -20, backgroundColor: "rgba(248, 81, 73, 0.1)" }}
                                        transition={{ duration: 0.2 }}
                                        className={`hover:bg-[var(--card-hover)] transition-colors group ${selectedIds.has(item.id) ? "bg-primary/5" : ""}`}
                                    >
                                        <td className="px-4 py-4">
                                            <button onClick={() => toggleSelect(item.id)} className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">
                                                {selectedIds.has(item.id) ? <CheckSquare className="w-4 h-4 text-primary" /> : <Square className="w-4 h-4" />}
                                            </button>
                                        </td>
                                        <td className="px-4 py-4 text-[var(--text-muted)] font-mono text-xs">{item.id.substring(0, 13)}...</td>
                                        <td className="px-4 py-4">
                                            <div className="flex flex-col">
                                                <span className="font-semibold text-[var(--text-primary)]">{item.name}</span>
                                                <span className="text-xs text-primary/60 font-medium mt-0.5">{item.category_id}</span>
                                            </div>
                                        </td>
                                        <td className="px-4 py-4 font-medium text-[var(--text-primary)]">₹{item.price}</td>
                                        <td className="px-4 py-4">
                                            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20">
                                                {item.quantity} {item.unit}
                                            </span>
                                        </td>
                                        <td className="px-4 py-4 text-right">
                                            <div className="flex justify-end gap-2">
                                                <button
                                                    onClick={() => onEditClick(item)}
                                                    className="inline-flex items-center justify-center w-8 h-8 rounded-md bg-[var(--card-bg)] hover:bg-[var(--card-hover)] border border-[var(--border)] text-primary transition-colors focus:ring-2 focus:ring-primary/50"
                                                    title="Edit"
                                                >
                                                    <Edit2 className="w-4 h-4" />
                                                </button>
                                                <button
                                                    onClick={() => onDeleteClick(item)}
                                                    className="inline-flex items-center justify-center w-8 h-8 rounded-md bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 text-red-500 transition-colors focus:ring-2 focus:ring-red-500/50"
                                                    title="Delete"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </td>
                                    </motion.tr>
                                ))}
                            </AnimatePresence>
                        </tbody>
                    </table>
                </div>
            )}

            {items.length > 0 && totalPages > 1 && (
                <div className="flex items-center justify-between mt-6 px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-xl text-sm">
                    <span className="text-[var(--text-muted)]">
                        Page <span className="font-medium text-[var(--text-primary)]">{currentPage}</span> of <span className="font-medium text-[var(--text-primary)]">{totalPages}</span>
                    </span>
                    <div className="flex gap-2">
                        <button
                            onClick={() => onPageChange(currentPage - 1)}
                            disabled={currentPage === 1}
                            className="px-4 py-1.5 bg-[var(--card-bg)] hover:bg-[var(--card-hover)] disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors text-[var(--text-primary)] font-medium"
                        >
                            Previous
                        </button>
                        <button
                            onClick={() => onPageChange(currentPage + 1)}
                            disabled={currentPage === totalPages}
                            className="px-4 py-1.5 bg-[var(--card-bg)] hover:bg-[var(--card-hover)] disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors text-[var(--text-primary)] font-medium"
                        >
                            Next
                        </button>
                    </div>
                </div>
            )}
        </motion.div>
    );
}
