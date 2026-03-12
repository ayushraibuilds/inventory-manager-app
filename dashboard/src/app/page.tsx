"use client";

import { motion, type Variants } from "framer-motion";
import Link from "next/link";
import {
  Activity,
  ArrowRight,
  AudioLines,
  BarChart3,
  Boxes,
  Camera,
  FileSpreadsheet,
  Globe2,
  Languages,
  MessageCircle,
  RefreshCcw,
  ShieldCheck,
  Sparkles,
  Store,
  Tags,
  Truck,
  Zap,
} from "lucide-react";
import ThemeToggle from "@/components/ThemeToggle";

const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 28 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] } },
};

const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.12 },
  },
};

const implementedFeatures = [
  {
    icon: MessageCircle,
    title: "WhatsApp AI catalog updates",
    desc: "Add, edit, or remove inventory with plain WhatsApp messages instead of a back-office workflow.",
    color: "text-emerald-500",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
  },
  {
    icon: AudioLines,
    title: "Voice note support",
    desc: "Sellers can send Hindi or English voice notes and the app turns them into catalog updates.",
    color: "text-sky-500",
    bg: "bg-sky-500/10",
    border: "border-sky-500/20",
  },
  {
    icon: Camera,
    title: "Image recognition",
    desc: "Send a product photo and extract item details into inventory instead of typing everything manually.",
    color: "text-fuchsia-500",
    bg: "bg-fuchsia-500/10",
    border: "border-fuchsia-500/20",
  },
  {
    icon: FileSpreadsheet,
    title: "CSV import and export",
    desc: "Bulk import stock, export the full catalog, and work with spreadsheet-based seller operations.",
    color: "text-amber-500",
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
  },
  {
    icon: BarChart3,
    title: "Realtime dashboard",
    desc: "See catalog value, low-stock counts, activity, and product changes in one place.",
    color: "text-blue-500",
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
  },
  {
    icon: Zap,
    title: "Low-stock alerts",
    desc: "Get WhatsApp reminders before fast-moving inventory drops too low.",
    color: "text-orange-500",
    bg: "bg-orange-500/10",
    border: "border-orange-500/20",
  },
  {
    icon: Languages,
    title: "Multilingual workflows",
    desc: "Built for sellers who mix English, Hindi, Hinglish, and other Indian languages in day-to-day operations.",
    color: "text-violet-500",
    bg: "bg-violet-500/10",
    border: "border-violet-500/20",
  },
  {
    icon: Tags,
    title: "Price intelligence",
    desc: "Compare seller pricing with market ranges and spot items priced too high or too low.",
    color: "text-rose-500",
    bg: "bg-rose-500/10",
    border: "border-rose-500/20",
  },
  {
    icon: RefreshCcw,
    title: "Batch price updates",
    desc: "Push multiple price corrections together instead of editing each item one by one.",
    color: "text-cyan-500",
    bg: "bg-cyan-500/10",
    border: "border-cyan-500/20",
  },
  {
    icon: Truck,
    title: "Order and activity tracking",
    desc: "Keep order state, recent actions, and seller-side operations visible from the dashboard.",
    color: "text-lime-500",
    bg: "bg-lime-500/10",
    border: "border-lime-500/20",
  },
];

const pricingPlans = [
  {
    id: "free",
    name: "Free",
    price: "₹0",
    cadence: "/month",
    summary: "For sellers getting started with WhatsApp-led inventory control.",
    points: ["100 products", "100 WhatsApp messages/month", "Basic dashboard"],
  },
  {
    id: "pro",
    name: "Pro",
    price: "₹199",
    cadence: "/month",
    summary: "For active sellers who need voice notes, image recognition, and unlimited scale.",
    points: ["Unlimited products", "Voice notes", "Image recognition", "Priority support"],
  },
  {
    id: "enterprise",
    name: "Enterprise",
    price: "₹999",
    cadence: "/month",
    summary: "For larger operations that need commercial support and deeper integrations.",
    points: ["Multi-store", "API access", "Custom branding", "ONDC listing support"],
  },
];

export default function LandingPage() {
  const scrollToFeatures = () => {
    document.getElementById("features")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] overflow-hidden">
      <nav className="fixed top-0 inset-x-0 z-50 bg-[var(--bg-primary)]/80 backdrop-blur-md border-b border-[var(--border)]">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <Link
            href="/"
            aria-label="Go to Super Seller home"
            className="flex items-center gap-3 rounded-xl transition-opacity hover:opacity-85"
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <Store className="w-4 h-4 text-white" />
            </div>
            <div>
              <span className="text-xl font-bold text-[var(--text-primary)] tracking-tight">
                Super Seller
              </span>
              <p className="text-xs text-[var(--text-muted)]">WhatsApp inventory control for sellers</p>
            </div>
          </Link>

          <div className="flex items-center gap-4">
            <ThemeToggle />
            <Link
              href="/login"
              className="text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors hidden sm:block"
            >
              Log in
            </Link>
            <Link
              href="/signup"
              className="px-5 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white text-sm font-semibold rounded-full shadow-lg shadow-emerald-500/25 transition-all hover:scale-105 active:scale-95"
            >
              Start Free
            </Link>
          </div>
        </div>
      </nav>

      <section className="relative pt-32 pb-20 lg:pt-44 lg:pb-28 px-6">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[880px] h-[880px] bg-emerald-500/10 rounded-full blur-[140px] pointer-events-none -z-10" />
        <div className="absolute top-0 right-0 w-[540px] h-[540px] bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none -z-10" />

        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-5xl mx-auto">
            <motion.div initial="hidden" animate="visible" variants={staggerContainer} className="space-y-8">
              <motion.div
                variants={fadeInUp}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-sm font-medium mb-4"
              >
                <Sparkles className="w-4 h-4" />
                Inventory updates by text, voice note, or image
              </motion.div>

              <motion.h1
                variants={fadeInUp}
                className="text-5xl lg:text-7xl font-extrabold text-[var(--text-primary)] tracking-tight leading-[1.05]"
              >
                Manage your inventory
                <br />
                <span className="inline-block relative">
                  <span className="relative z-10 bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-400 bg-clip-text text-transparent">
                    directly from WhatsApp.
                  </span>
                </span>
              </motion.h1>

              <motion.p
                variants={fadeInUp}
                className="text-xl text-[var(--text-secondary)] leading-relaxed max-w-3xl mx-auto"
              >
                Super Seller is for sellers who want fast catalog maintenance, not another complex panel.
                Add stock, update prices, review low inventory, import CSVs, track activity, and monitor
                pricing from a dashboard that stays in sync with WhatsApp.
              </motion.p>

              <motion.div
                variants={fadeInUp}
                className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4"
              >
                <Link
                  href="/signup"
                  className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-bold rounded-xl shadow-xl shadow-emerald-500/25 transition-all hover:-translate-y-1 flex items-center justify-center gap-2 text-lg"
                >
                  Start Managing Inventory <ArrowRight className="w-5 h-5" />
                </Link>
                <button
                  type="button"
                  onClick={scrollToFeatures}
                  className="w-full sm:w-auto px-8 py-4 bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text-primary)] font-bold rounded-xl shadow-sm hover:bg-[var(--card-hover)] transition-all flex items-center justify-center gap-2 text-lg"
                >
                  See implemented features
                </button>
              </motion.div>

              <motion.p variants={fadeInUp} className="text-sm text-[var(--text-muted)] pt-2">
                Free to use • Seller-focused workflow • Works with your existing WhatsApp habit
              </motion.p>
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.45, duration: 0.8 }}
            className="mt-18 relative mx-auto w-full max-w-6xl rounded-2xl md:rounded-[2rem] border border-[var(--border)] bg-[#091015] shadow-2xl overflow-hidden shadow-emerald-500/10"
          >
            <div className="h-10 border-b border-white/10 bg-white/5 flex items-center px-4 gap-2">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-500/80" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                <div className="w-3 h-3 rounded-full bg-green-500/80" />
              </div>
              <div className="mx-auto px-3 py-1 bg-white/5 rounded-md flex items-center gap-2 text-xs text-white/40 max-w-[220px] w-full justify-center">
                <ShieldCheck className="w-3 h-3" />
                dashboard.superseller.in
              </div>
            </div>

            <div className="relative p-5 md:p-8 bg-[radial-gradient(circle_at_top_left,_rgba(16,185,129,0.18),_transparent_30%),radial-gradient(circle_at_bottom_right,_rgba(34,211,238,0.14),_transparent_28%),linear-gradient(180deg,#071018_0%,#0A131B_100%)]">
              <div className="grid grid-cols-1 lg:grid-cols-[1.25fr_0.95fr] gap-6 items-stretch">
                <div className="rounded-[1.6rem] border border-white/8 bg-white/5 backdrop-blur-md p-5 md:p-6">
                  <div className="flex items-start justify-between gap-4 mb-6">
                    <div>
                      <p className="text-xs uppercase tracking-[0.22em] text-emerald-300/70 mb-2">Seller inventory snapshot</p>
                      <h3 className="text-2xl font-bold text-white">See what stays visible after each WhatsApp update</h3>
                    </div>
                    <div className="rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-xs font-semibold text-emerald-300">
                      Live catalog context
                    </div>
                  </div>

                  <div className="grid sm:grid-cols-2 gap-4 mb-6">
                    <div className="rounded-2xl border border-emerald-400/15 bg-emerald-400/8 p-4">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-10 h-10 rounded-xl bg-emerald-400/15 border border-emerald-400/20 flex items-center justify-center">
                          <Boxes className="w-5 h-5 text-emerald-300" />
                        </div>
                        <div>
                          <p className="text-xs text-white/50 uppercase tracking-[0.18em]">Products tracked</p>
                          <p className="text-white font-semibold">26 active products</p>
                        </div>
                      </div>
                      <p className="text-sm text-white/70">
                        Stock, pricing, units, and categories stay organized even when updates come from chat, image, or CSV.
                      </p>
                    </div>

                    <div className="rounded-2xl border border-cyan-400/15 bg-cyan-400/8 p-4">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-10 h-10 rounded-xl bg-cyan-400/15 border border-cyan-400/20 flex items-center justify-center">
                          <Activity className="w-5 h-5 text-cyan-300" />
                        </div>
                        <div>
                          <p className="text-xs text-white/50 uppercase tracking-[0.18em]">Catalog health</p>
                          <p className="text-white font-semibold">₹4,200 total value</p>
                        </div>
                      </div>
                      <p className="text-sm text-white/70">
                        Low-stock alerts, pricing checks, and recent activity keep sellers aware of what needs action next.
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-3 mb-4">
                    {[
                      { label: "Low stock", value: "3 items", tone: "text-amber-300 border-amber-400/20 bg-amber-400/8" },
                      { label: "Images processed", value: "12 today", tone: "text-cyan-300 border-cyan-400/20 bg-cyan-400/8" },
                      { label: "Price gaps", value: "4 flagged", tone: "text-rose-300 border-rose-400/20 bg-rose-400/8" },
                    ].map((stat) => (
                      <div key={stat.label} className={`rounded-2xl border px-4 py-3 ${stat.tone}`}>
                        <p className="text-[11px] uppercase tracking-[0.16em] opacity-75">{stat.label}</p>
                        <p className="mt-2 text-lg font-bold text-white">{stat.value}</p>
                      </div>
                    ))}
                  </div>

                  <div className="rounded-[1.4rem] border border-white/8 bg-black/20 overflow-hidden">
                    <div className="grid grid-cols-[1.3fr_0.7fr_0.7fr] gap-3 px-4 py-3 border-b border-white/8 text-[11px] uppercase tracking-[0.16em] text-white/45">
                      <span>Item</span>
                      <span>Stock</span>
                      <span>Status</span>
                    </div>
                    {[
                      { name: "Aashirvaad Atta 5kg", stock: "12 packs", status: "Healthy", tone: "text-emerald-300" },
                      { name: "Tata Salt 1kg", stock: "3 packs", status: "Low", tone: "text-amber-300" },
                      { name: "Maggi 12-pack", stock: "18 packs", status: "Updated", tone: "text-cyan-300" },
                    ].map((row) => (
                      <div
                        key={row.name}
                        className="grid grid-cols-[1.3fr_0.7fr_0.7fr] gap-3 px-4 py-3 border-b last:border-b-0 border-white/6 text-sm"
                      >
                        <span className="text-white/82">{row.name}</span>
                        <span className="text-white/64">{row.stock}</span>
                        <span className={`font-semibold ${row.tone}`}>{row.status}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-[1.8rem] border border-white/8 bg-[#0b141a] shadow-2xl overflow-hidden flex flex-col">
                  <div className="h-14 bg-[#0f7a69] flex items-center px-4 gap-3 text-white">
                    <MessageCircle className="w-5 h-5" />
                    <div className="flex-1">
                      <h4 className="font-semibold text-sm">Super Seller Bot</h4>
                      <p className="text-[10px] text-white/70">catalog assistant</p>
                    </div>
                  </div>
                  <div className="flex-1 bg-[#E9DED4] p-4 flex flex-col gap-3">
                    <div className="bg-[#DCF8C6] p-3 rounded-2xl rounded-tr-none self-end max-w-[82%] shadow-sm">
                      <p className="text-gray-800 text-xs">10 packet Maggi at 18, 6 Coke bottles at 40</p>
                    </div>
                    <div className="bg-white p-3 rounded-2xl rounded-tl-none self-start max-w-[86%] shadow-sm">
                      <p className="font-semibold text-emerald-700 mb-1 text-xs">Catalog updated</p>
                      <p className="text-gray-800 text-xs">Added Maggi and Coke. Catalog now has 26 items.</p>
                    </div>
                    <div className="bg-[#DCF8C6] p-3 rounded-2xl rounded-tr-none self-end max-w-[82%] shadow-sm">
                      <p className="text-gray-800 text-xs">Sending image for biscuit stock</p>
                    </div>
                    <div className="bg-white p-3 rounded-2xl rounded-tl-none self-start max-w-[86%] shadow-sm">
                      <p className="font-semibold text-cyan-700 mb-1 text-xs">Photo processed</p>
                      <p className="text-gray-800 text-xs">Detected 4 items from the image and matched 2 existing products.</p>
                    </div>
                    <div className="bg-white p-3 rounded-2xl rounded-tl-none self-start max-w-[86%] shadow-sm">
                      <p className="font-semibold text-amber-700 mb-1 text-xs">Low stock alert</p>
                      <p className="text-gray-800 text-xs">Salt is down to 3 units. Review stock from the dashboard.</p>
                    </div>
                  </div>
                  <div className="border-t border-black/10 bg-white px-4 py-3 text-[11px] text-slate-500">
                    Inventory stays synced between WhatsApp updates and the dashboard.
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <section id="how-it-works" className="py-24 bg-[var(--card-bg)] border-y border-[var(--border)]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold text-[var(--text-primary)] mb-4">
              Built for sellers who already work on WhatsApp
            </h2>
            <p className="text-lg text-[var(--text-secondary)]">
              The app keeps inventory work lightweight: talk to WhatsApp for updates, then use the
              dashboard for visibility and control.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-[var(--bg-primary)] p-8 rounded-3xl border border-[var(--border)] relative overflow-hidden group hover:border-emerald-500/50 transition-colors">
              <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-bl-full -z-10 transition-transform group-hover:scale-110" />
              <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-6">
                <MessageCircle className="w-7 h-7 text-emerald-500" />
              </div>
              <h3 className="text-xl font-bold text-[var(--text-primary)] mb-3">1. Connect WhatsApp</h3>
              <p className="text-[var(--text-secondary)] leading-relaxed">
                Link the seller phone number once, then manage inventory from the chat window sellers
                already use every day.
              </p>
            </div>

            <div className="bg-[var(--bg-primary)] p-8 rounded-3xl border border-[var(--border)] relative overflow-hidden group hover:border-cyan-500/50 transition-colors">
              <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/10 rounded-bl-full -z-10 transition-transform group-hover:scale-110" />
              <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mb-6">
                <Globe2 className="w-7 h-7 text-cyan-500" />
              </div>
              <h3 className="text-xl font-bold text-[var(--text-primary)] mb-3">2. Update inventory naturally</h3>
              <p className="text-[var(--text-secondary)] leading-relaxed">
                Type a message, send a voice note, or upload a product photo. AI extracts products,
                price, quantity, and updates your catalog.
              </p>
            </div>

            <div className="bg-[var(--bg-primary)] p-8 rounded-3xl border border-[var(--border)] relative overflow-hidden group hover:border-violet-500/50 transition-colors">
              <div className="absolute top-0 right-0 w-32 h-32 bg-violet-500/10 rounded-bl-full -z-10 transition-transform group-hover:scale-110" />
              <div className="w-14 h-14 rounded-2xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center mb-6">
                <BarChart3 className="w-7 h-7 text-violet-500" />
              </div>
              <h3 className="text-xl font-bold text-[var(--text-primary)] mb-3">3. Track everything</h3>
              <p className="text-[var(--text-secondary)] leading-relaxed">
                Monitor catalog value, stock levels, activity logs, price gaps, imports, and seller-side
                operations from the dashboard.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-end justify-between mb-16 gap-6">
            <div className="max-w-3xl">
              <h2 className="text-3xl lg:text-4xl font-bold text-[var(--text-primary)] mb-4">
                What sellers already get
              </h2>
              <p className="text-lg text-[var(--text-secondary)]">
                This is not a placeholder feature list. These workflows are already implemented in the
                product and available across the dashboard and WhatsApp automation flows.
              </p>
            </div>
            <Link
              href="/signup"
              className="px-6 py-3 bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text-primary)] font-semibold rounded-xl hover:bg-[var(--card-hover)] transition-all flex items-center gap-2"
            >
              Start with seller signup <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {implementedFeatures.map((feature) => (
              <div
                key={feature.title}
                className="p-6 rounded-2xl bg-[var(--card-bg)] border border-[var(--border)] hover:shadow-xl hover:-translate-y-1 transition-all"
              >
                <div className={`w-12 h-12 rounded-xl ${feature.bg} ${feature.border} border flex items-center justify-center mb-5`}>
                  <feature.icon className={`w-6 h-6 ${feature.color}`} />
                </div>
                <h4 className="text-lg font-bold text-[var(--text-primary)] mb-2">{feature.title}</h4>
                <p className="text-[var(--text-secondary)] leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="pricing" className="py-24 px-6 bg-[var(--card-bg)] border-y border-[var(--border)]">
        <div className="max-w-7xl mx-auto">
          <div className="max-w-3xl mb-14">
            <h2 className="text-3xl lg:text-4xl font-bold text-[var(--text-primary)] mb-4">Simple pricing for seller inventory teams</h2>
            <p className="text-lg text-[var(--text-secondary)]">
              The free tier is enough to validate the workflow. Pro unlocks the real WhatsApp automation edge.
              Enterprise adds commercial rollout features for bigger seller operations.
            </p>
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            {pricingPlans.map((plan) => (
              <div
                key={plan.id}
                className={`rounded-3xl border p-6 shadow-xl ${
                  plan.id === "pro"
                    ? "border-emerald-500/30 bg-emerald-500/5"
                    : "border-[var(--border)] bg-[var(--bg-primary)]"
                }`}
              >
                <div className="mb-5 flex items-start justify-between gap-4">
                  <div>
                    <h3 className="text-2xl font-bold text-[var(--text-primary)]">{plan.name}</h3>
                    <p className="mt-2 text-sm text-[var(--text-secondary)]">{plan.summary}</p>
                  </div>
                  {plan.id === "pro" && (
                    <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-500">
                      Popular
                    </span>
                  )}
                </div>
                <p className="mb-5 text-4xl font-extrabold text-[var(--text-primary)]">
                  {plan.price}
                  <span className="ml-1 text-base font-medium text-[var(--text-muted)]">{plan.cadence}</span>
                </p>
                <ul className="space-y-3 text-sm text-[var(--text-secondary)]">
                  {plan.points.map((point) => (
                    <li key={point} className="flex items-start gap-2">
                      <span className="mt-1 h-2 w-2 rounded-full bg-emerald-500" />
                      <span>{point}</span>
                    </li>
                  ))}
                </ul>
                <Link
                  href="/signup"
                  className={`mt-6 inline-flex w-full items-center justify-center rounded-xl px-4 py-3 text-sm font-semibold transition-all ${
                    plan.id === "pro"
                      ? "bg-gradient-to-r from-emerald-500 to-teal-600 text-white hover:from-emerald-400 hover:to-teal-500"
                      : "border border-[var(--border)] bg-[var(--card-bg)] text-[var(--text-primary)] hover:bg-[var(--card-hover)]"
                  }`}
                >
                  Start with {plan.name}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-28 px-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-emerald-500/5 to-transparent pointer-events-none" />
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <h2 className="text-4xl lg:text-6xl font-extrabold text-[var(--text-primary)] mb-6 tracking-tight">
            Start managing your inventory today
          </h2>
          <p className="text-xl text-[var(--text-secondary)] mb-10 max-w-2xl mx-auto">
            Join sellers who want a faster way to keep stock, pricing, and catalog data up to date
            without moving their workflow away from WhatsApp.
          </p>
          <Link
            href="/signup"
            className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-bold rounded-xl shadow-2xl shadow-emerald-500/25 hover:scale-105 transition-all text-lg"
          >
            Create seller workspace <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      <footer className="py-12 border-t border-[var(--border)] bg-[var(--bg-primary)]">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
          <Link
            href="/"
            aria-label="Go to Super Seller home"
            className="flex items-center gap-2 rounded-lg transition-opacity hover:opacity-85"
          >
            <Store className="w-5 h-5 text-emerald-500" />
            <span className="font-bold text-[var(--text-primary)]">Super Seller</span>
          </Link>
          <p className="text-[var(--text-secondary)] text-sm text-center">
            © {new Date().getFullYear()} ONDC Super Seller. WhatsApp-first inventory management for sellers.
          </p>
          <div className="flex gap-4">
            <Link href="/privacy" className="text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">
              Privacy
            </Link>
            <Link href="/terms" className="text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">
              Terms
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
