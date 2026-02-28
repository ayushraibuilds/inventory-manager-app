import { motion, AnimatePresence } from "framer-motion";
import { Edit2, Plus } from "lucide-react";

interface ProductFormData {
    name: string;
    price: string;
    quantity: number;
    unit: string;
    category_id: string;
}

interface ProductModalProps {
    isOpen: boolean;
    isEditing: boolean;
    formData: ProductFormData;
    setFormData: (data: ProductFormData) => void;
    onSubmit: (e: React.FormEvent) => void;
    onClose: () => void;
}

export default function ProductModal({
    isOpen,
    isEditing,
    formData,
    setFormData,
    onSubmit,
    onClose
}: ProductModalProps) {
    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                        onClick={onClose}
                    />
                    <motion.div
                        initial={{ scale: 0.95, opacity: 0, y: 20 }}
                        animate={{ scale: 1, opacity: 1, y: 0 }}
                        exit={{ scale: 0.95, opacity: 0, y: 20 }}
                        className="relative w-full max-w-lg bg-[var(--bg-primary)] border border-[var(--border)] rounded-2xl shadow-2xl overflow-hidden"
                    >
                        <div className="px-6 py-5 border-b border-[var(--border)] bg-[var(--card-bg)]">
                            <h3 className="text-xl font-bold text-[var(--text-primary)] flex items-center gap-2">
                                {isEditing ? <Edit2 className="w-5 h-5 text-primary" /> : <Plus className="w-5 h-5 text-primary" />}
                                {isEditing ? "Edit Product" : "Add New Product"}
                            </h3>
                        </div>
                        <form onSubmit={onSubmit} className="p-6 space-y-5">
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Product Name</label>
                                    <input
                                        required
                                        value={formData.name}
                                        onChange={e => setFormData({ ...formData, name: e.target.value })}
                                        className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-lg px-4 py-2.5 text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all placeholder-[var(--text-muted)]"
                                        placeholder="e.g. Aashirvaad Atta"
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Price (INR)</label>
                                        <div className="relative">
                                            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]">₹</span>
                                            <input
                                                required
                                                type="number"
                                                min="0"
                                                value={formData.price}
                                                onChange={e => setFormData({ ...formData, price: e.target.value })}
                                                className="w-full pl-8 pr-4 py-2.5 bg-[var(--input-bg)] border border-[var(--input-border)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                                                placeholder="0.00"
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Stock Quantity</label>
                                        <input
                                            required
                                            type="number"
                                            min="0"
                                            value={formData.quantity}
                                            onChange={e => setFormData({ ...formData, quantity: parseInt(e.target.value) || 0 })}
                                            className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-lg px-4 py-2.5 text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Unit Type</label>
                                        <select
                                            required
                                            value={formData.unit}
                                            onChange={e => setFormData({ ...formData, unit: e.target.value })}
                                            className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-lg px-4 py-2.5 text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all appearance-none"
                                        >
                                            <option value="piece">Piece (pc)</option>
                                            <option value="kg">Kilogram (kg)</option>
                                            <option value="liter">Liter (L)</option>
                                            <option value="dozen">Dozen</option>
                                            <option value="box">Box / Bori</option>
                                            <option value="packet">Packet</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Category</label>
                                        <select
                                            required
                                            value={formData.category_id}
                                            onChange={e => setFormData({ ...formData, category_id: e.target.value })}
                                            className="w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-lg px-4 py-2.5 text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all appearance-none"
                                        >
                                            <option value="Grocery">Grocery</option>
                                            <option value="F&B">Food & Beverage</option>
                                            <option value="Home & Decor">Home & Decor</option>
                                            <option value="Health & Wellness">Health & Wellness</option>
                                            <option value="Electronics">Electronics</option>
                                            <option value="Beauty & Personal Care">Beauty & Personal Care</option>
                                            <option value="Other">Other</option>
                                        </select>
                                    </div>
                                </div>
                            </div>

                            <div className="flex gap-3 pt-4 border-t border-[var(--border)] mt-6">
                                <button
                                    type="submit"
                                    className="flex-1 bg-primary hover:bg-blue-500 text-white font-medium py-2.5 rounded-lg transition-all active:scale-95 flex justify-center items-center gap-2 shadow-lg shadow-primary/20"
                                >
                                    {isEditing ? "Save Changes" : "Create Listing"}
                                </button>
                                <button
                                    type="button"
                                    onClick={onClose}
                                    className="flex-1 bg-[var(--card-bg)] hover:bg-[var(--card-hover)] text-[var(--text-primary)] font-medium py-2.5 rounded-lg border border-[var(--border)] transition-all active:scale-95"
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}
