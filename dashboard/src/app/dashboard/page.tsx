"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import { Toaster, toast } from "sonner";
import { Activity, Truck, LogOut, BarChart3, User, ShoppingCart, Upload } from "lucide-react";
import Link from "next/link";
import StatCards from "../../components/StatCards";
import InventoryTable, { CatalogItem } from "../../components/InventoryTable";
import ProductModal from "../../components/ProductModal";
import ConfirmDialog from "../../components/ConfirmDialog";
import ActivityLog from "../../components/ActivityLog";
import ThemeToggle from "../../components/ThemeToggle";
import { useAuth } from "@/components/AuthProvider";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

export default function Dashboard() {
  const { sellerId, logout, isLoading } = useAuth();
  const activeSellerId = sellerId || "";

  const [items, setItems] = useState<CatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Pagination & Analytics State
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalValue, setTotalValue] = useState(0);
  const [lowStockCount, setLowStockCount] = useState(0);
  const [totalProducts, setTotalProducts] = useState(0);
  const LIMIT = 10;

  // Delete confirmation state
  const [deleteTarget, setDeleteTarget] = useState<{ items: CatalogItem[]; bulk: boolean } | null>(null);

  // SSE ref
  const eventSourceRef = useRef<EventSource | null>(null);

  const [formData, setFormData] = useState({
    name: "",
    price: "",
    quantity: 1,
    unit: "piece",
    category_id: "Grocery"
  });

  const fetchCatalog = useCallback(async (showToast = false, page = currentPage) => {
    if (!activeSellerId) return;
    try {
      if (showToast) setIsRefreshing(true);
      const offset = (page - 1) * LIMIT;
      const res = await fetch(`${API_URL}/api/catalog?limit=${LIMIT}&offset=${offset}&seller_id=${encodeURIComponent(activeSellerId)}`, { cache: "no-store" });

      if (res.status === 429) {
        if (showToast) toast.error("Rate limit exceeded. Please wait a moment.");
        throw new Error("Rate limit exceeded");
      }
      if (!res.ok) throw new Error("Network response was not ok");
      const data = await res.json();

      if (data && data.pagination) {
        setTotalProducts(data.pagination.total_count || 0);
        setTotalPages(Math.ceil((data.pagination.total_count || 0) / LIMIT) || 1);
        setTotalValue(data.pagination.total_value || 0);
        setLowStockCount(data.pagination.low_stock_count || 0);
      } else {
        setTotalProducts(0); setTotalPages(1); setTotalValue(0); setLowStockCount(0);
      }

      if (data && data["bpp/catalog"]) {
        const providers = data["bpp/catalog"]["bpp/providers"] || [];
        if (providers.length > 0 && providers[0].items) {
          interface RawCatalogItem {
            id: string;
            price?: { value?: string };
            quantity?: { available?: { count?: number } };
            descriptor?: { name?: string; short_desc?: string };
          }
          const formattedItems = providers[0].items.map((item: RawCatalogItem) => {
            let unitFallback = "unit";
            if (item.descriptor?.short_desc) {
              const parts = item.descriptor.short_desc.split(" ");
              if (parts.length > 1) unitFallback = parts[1];
            }
            return {
              id: item.id,
              name: item.descriptor?.name || "Unknown",
              price: item.price?.value || "0",
              quantity: item.quantity?.available?.count || 0,
              unit: unitFallback,
              category_id: (item as any).category_id || "Grocery"
            };
          });
          setItems(formattedItems);
        } else { setItems([]); }
      } else { setItems([]); }
      if (showToast) toast.success("Catalog synced successfully.");
    } catch (error) {
      console.error("Failed to fetch catalog:", error);
      if (showToast) toast.error("Failed to sync catalog.");
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [currentPage, activeSellerId]);

  // SSE
  useEffect(() => {
    if (!activeSellerId || isLoading) return;
    fetchCatalog();
    const es = new EventSource(`${API_URL}/api/catalog/stream?seller_id=${encodeURIComponent(activeSellerId)}`);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.error) return;
        setTotalProducts(data.total_count || 0);
        setTotalValue(data.total_value || 0);
        setLowStockCount(data.low_stock_count || 0);
        if (data.items) {
          const offset = (currentPage - 1) * LIMIT;
          const paginatedItems = data.items.slice(offset, offset + LIMIT);
          setTotalPages(Math.ceil((data.total_count || 0) / LIMIT) || 1);
          const formattedItems = paginatedItems.map((item: any) => {
            let unitFallback = "unit";
            if (item.descriptor?.short_desc) {
              const parts = item.descriptor.short_desc.split(" ");
              if (parts.length > 1) unitFallback = parts[1];
            }
            return {
              id: item.id,
              name: item.descriptor?.name || "Unknown",
              price: item.price?.value || "0",
              quantity: item.quantity?.available?.count || 0,
              unit: unitFallback,
              category_id: item.category_id || "Grocery"
            };
          });
          setItems(formattedItems);
          setLoading(false);
        }
      } catch { /* heartbeat */ }
    };
    es.onerror = () => {
      es.close();
      const interval = setInterval(() => fetchCatalog(false, currentPage), 5000);
      return () => clearInterval(interval);
    };
    return () => { es.close(); };
  }, [activeSellerId, currentPage, isLoading, fetchCatalog]);

  // --- CRUD handlers ---
  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSellerId) return;
    const loadingToast = toast.loading("Adding product...");
    try {
      const res = await fetch(`${API_URL}/api/catalog/item`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
        body: JSON.stringify({ name: formData.name, price: formData.price.toString(), quantity: formData.quantity, unit: formData.unit, seller_id: activeSellerId })
      });
      if (res.status === 429) {
        toast.error("Too many requests. Please slow down.", { id: loadingToast });
        return;
      }
      if (res.ok) {
        setShowAddModal(false);
        setFormData({ name: "", price: "", quantity: 1, unit: "piece", category_id: "Grocery" });
        await fetchCatalog();
        toast.success(`${formData.name} added!`, { id: loadingToast });
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || "Failed to add product.", { id: loadingToast });
      }
    } catch { toast.error("Network error.", { id: loadingToast }); }
  };

  const confirmDelete = (item: CatalogItem) => {
    setDeleteTarget({ items: [item], bulk: false });
  };

  const confirmBulkDelete = (items: CatalogItem[]) => {
    setDeleteTarget({ items, bulk: true });
  };

  const executeDelete = async () => {
    if (!deleteTarget || !activeSellerId) return;
    const { items: targetItems, bulk } = deleteTarget;
    setDeleteTarget(null);

    if (bulk && targetItems.length > 1) {
      const loadingToast = toast.loading(`Deleting ${targetItems.length} items...`);
      try {
        const res = await fetch(`${API_URL}/api/catalog/bulk-delete`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
          body: JSON.stringify({ seller_id: activeSellerId, item_ids: targetItems.map(i => i.id) })
        });
        if (res.status === 429) {
          toast.error("Too many requests. Please slow down.", { id: loadingToast });
          return;
        }
        if (res.ok) {
          await fetchCatalog();
          toast.success(`${targetItems.length} items deleted.`, { id: loadingToast });
        } else { toast.error("Failed to delete.", { id: loadingToast }); }
      } catch { toast.error("Network error.", { id: loadingToast }); }
    } else {
      const item = targetItems[0];
      const loadingToast = toast.loading(`Deleting ${item.name}...`);
      try {
        const res = await fetch(`${API_URL}/api/catalog/item/${item.id}?seller_id=${encodeURIComponent(activeSellerId)}`, { method: "DELETE", headers: { "X-API-Key": API_KEY } });
        if (res.status === 429) {
          toast.error("Too many requests. Please slow down.", { id: loadingToast });
          return;
        }
        if (res.ok) {
          await fetchCatalog();
          toast.success(`${item.name} deleted.`, { id: loadingToast });
        } else { toast.error("Failed to delete.", { id: loadingToast }); }
      } catch { toast.error("Network error.", { id: loadingToast }); }
    }
  };

  const handleEditClick = (item: CatalogItem) => {
    setEditingItemId(item.id);
    setFormData({ name: item.name, price: item.price, quantity: item.quantity, unit: item.unit, category_id: item.category_id });
    setShowAddModal(true);
  };

  const handleUpdateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingItemId || !activeSellerId) return;
    const loadingToast = toast.loading(`Updating ${formData.name}...`);
    try {
      const res = await fetch(`${API_URL}/api/catalog/item/${editingItemId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
        body: JSON.stringify({ name: formData.name, price: formData.price.toString(), quantity: parseInt(formData.quantity.toString(), 10), unit: formData.unit, seller_id: activeSellerId })
      });
      if (res.status === 429) {
        toast.error("Too many requests. Please slow down.", { id: loadingToast });
        return;
      }
      if (res.ok) {
        setShowAddModal(false);
        setEditingItemId(null);
        setFormData({ name: "", price: "", quantity: 1, unit: "piece", category_id: "Grocery" });
        await fetchCatalog();
        toast.success(`${formData.name} updated!`, { id: loadingToast });
      } else { toast.error("Failed to update.", { id: loadingToast }); }
    } catch { toast.error("Network error.", { id: loadingToast }); }
  };

  const [isMounted, setIsMounted] = useState(false);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'n') {
        e.preventDefault();
        setEditingItemId(null);
        setFormData({ name: "", price: "", quantity: 1, unit: "piece", category_id: "Grocery" });
        setShowAddModal(true);
      }
      if (e.key === 'Escape') {
        if (showAddModal) setShowAddModal(false);
        if (deleteTarget) setDeleteTarget(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showAddModal, deleteTarget]);

  useEffect(() => { setIsMounted(true); }, []);

  if (!isMounted || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  // Fallback for null activeSellerId handled by protected route wrapper, but just in case
  if (!activeSellerId) return null;

  return (
    <div className="max-w-7xl mx-auto p-4 md:p-8">
      <Toaster theme="dark" position="top-center" />

      {/* Header */}
      <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center py-6 border-b border-[var(--border)] mb-8 gap-4">
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-3xl font-extrabold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent tracking-tight"
        >
          ONDC Super Seller
        </motion.h1>
        <div className="flex items-center gap-3 flex-wrap">
          {/* Analytics Link */}
          <Link
            href="/analytics"
            className="flex items-center gap-2 bg-purple-500/10 border border-purple-500/20 text-purple-400 px-4 py-1.5 rounded-full font-semibold text-sm hover:bg-purple-500/20 transition-all"
          >
            <BarChart3 className="w-3.5 h-3.5" />
            Analytics
          </Link>

          {/* Orders Link */}
          <Link
            href="/orders"
            className="flex items-center gap-2 bg-orange-500/10 border border-orange-500/20 text-orange-400 px-4 py-1.5 rounded-full font-semibold text-sm hover:bg-orange-500/20 transition-all"
          >
            <ShoppingCart className="w-3.5 h-3.5" />
            Orders
          </Link>

          {/* Import Link */}
          <Link
            href="/import"
            className="flex items-center gap-2 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 px-4 py-1.5 rounded-full font-semibold text-sm hover:bg-cyan-500/20 transition-all"
          >
            <Upload className="w-3.5 h-3.5" />
            Import
          </Link>

          {/* Seller Profile Link */}
          <Link
            href={`/seller/${encodeURIComponent(activeSellerId)}`}
            className="flex items-center gap-2 bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text-primary)] px-4 py-1.5 rounded-full font-medium text-sm hover:bg-[var(--card-hover)] transition-all"
          >
            <User className="w-3.5 h-3.5 text-[var(--text-muted)]" />
            Profile
          </Link>

          {/* Logout Button */}
          <button
            onClick={logout}
            className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 text-red-500 px-4 py-1.5 rounded-full font-medium text-sm hover:bg-red-500/20 transition-all"
          >
            <LogOut className="w-3.5 h-3.5" />
            Logout
          </button>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-2 bg-green-500/10 border border-green-500/20 text-green-400 px-4 py-1.5 rounded-full font-semibold text-sm shadow-sm backdrop-blur-md"
          >
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
            </span>
            Network Live
          </motion.div>

          <ThemeToggle />
        </div>
      </header>

      <StatCards totalProducts={totalProducts} totalValue={totalValue} lowStockCount={lowStockCount} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <InventoryTable
            items={items}
            loading={loading}
            isRefreshing={isRefreshing}
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={(page) => { setCurrentPage(page); fetchCatalog(true, page); }}
            onRefresh={() => fetchCatalog(true)}
            onAddClick={() => {
              setEditingItemId(null);
              setFormData({ name: "", price: "", quantity: 1, unit: "piece", category_id: "Grocery" });
              setShowAddModal(true);
            }}
            onEditClick={handleEditClick}
            onDeleteClick={confirmDelete}
            onBulkDelete={confirmBulkDelete}
          />
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Activity Log */}
          <ActivityLog selectedSeller={activeSellerId} />

          {/* UPI Settlements */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-[var(--card-bg)] backdrop-blur-xl border border-[var(--border)] rounded-2xl p-6 shadow-2xl"
          >
            <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-accent" />
              UPI Settlements
            </h2>
            <div className="bg-gradient-to-b from-[var(--bg-primary)] to-[var(--card-bg)] border border-[var(--border)] border-dashed rounded-xl p-6 text-center text-[var(--text-muted)] hover:border-accent/50 hover:text-[var(--text-primary)] transition-all cursor-pointer group">
              <span className="text-4xl block mb-3 group-hover:scale-110 transition-transform">💸</span>
              <p className="font-medium text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]">Connect Bank Account</p>
              <p className="text-xs mt-1 opacity-70">for instant payouts</p>
            </div>
          </motion.div>

          {/* Logistics */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-[var(--card-bg)] backdrop-blur-xl border border-[var(--border)] rounded-2xl p-6 shadow-2xl"
          >
            <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
              <Truck className="w-5 h-5 text-purple-400" />
              Logistics Partners
            </h2>
            <div className="bg-gradient-to-b from-[var(--bg-primary)] to-[var(--card-bg)] border border-[var(--border)] border-dashed rounded-xl p-6 text-center text-[var(--text-muted)] hover:border-purple-400/50 hover:text-[var(--text-primary)] transition-all cursor-pointer group">
              <span className="text-4xl block mb-3 group-hover:scale-110 transition-transform">🚚</span>
              <p className="font-medium text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]">Dunzo & Shadowfax</p>
              <p className="text-xs mt-1 opacity-70">Integration pending</p>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Modals */}
      <ProductModal
        isOpen={showAddModal}
        isEditing={!!editingItemId}
        formData={formData}
        setFormData={setFormData}
        onSubmit={editingItemId ? handleUpdateSubmit : handleAddSubmit}
        onClose={() => setShowAddModal(false)}
      />

      <ConfirmDialog
        isOpen={!!deleteTarget}
        title={deleteTarget?.bulk && deleteTarget.items.length > 1 ? `Delete ${deleteTarget.items.length} items?` : `Delete ${deleteTarget?.items[0]?.name || "item"}?`}
        message={deleteTarget?.bulk && deleteTarget.items.length > 1
          ? `This will permanently remove ${deleteTarget.items.length} items from the catalog.`
          : `This will permanently remove "${deleteTarget?.items[0]?.name}" from the catalog. This action cannot be undone.`
        }
        onConfirm={executeDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
