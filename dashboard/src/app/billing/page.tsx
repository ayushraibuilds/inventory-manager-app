"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Check, Crown, MessageCircleMore, Wallet } from "lucide-react";
import Link from "next/link";
import { Toaster, toast } from "sonner";
import { useAuth } from "@/components/AuthProvider";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Plan = {
  id: string;
  name: string;
  price_inr: number;
  interval: string;
  description: string;
  limits: {
    products: number | null;
    whatsapp_messages: number | null;
  };
  features: string[];
};

type BillingSummary = {
  seller_id: string;
  current_plan: string;
  plans: Plan[];
  usage: {
    period_start: string;
    products: { used: number; limit: number | null; remaining: number | null };
    whatsapp_messages: { used: number; limit: number | null; remaining: number | null };
  };
};

declare global {
  interface Window {
    Razorpay?: new (options: Record<string, unknown>) => { open: () => void };
  }
}

function loadRazorpayScript() {
  return new Promise<boolean>((resolve) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

export default function BillingPage() {
  const { sellerId, token, isLoading: authLoading } = useAuth();
  const activeSellerId = sellerId || "";

  const [summary, setSummary] = useState<BillingSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionPlan, setActionPlan] = useState<string>("");

  const fetchSummary = useCallback(async () => {
    if (!activeSellerId || !token) return;
    try {
      const res = await fetch(
        `${API_URL}/api/billing/summary?seller_id=${encodeURIComponent(activeSellerId)}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) throw new Error("Failed to fetch billing summary");
      const data: BillingSummary = await res.json();
      setSummary(data);
    } catch {
      toast.error("Failed to load billing summary.");
    } finally {
      setLoading(false);
    }
  }, [activeSellerId, token]);

  useEffect(() => {
    if (!authLoading && activeSellerId && token) {
      void fetchSummary();
    }
  }, [authLoading, activeSellerId, token, fetchSummary]);

  const handlePlanAction = async (planId: string) => {
    if (!activeSellerId || !token) return;
    setActionPlan(planId);
    try {
      const checkoutRes = await fetch(`${API_URL}/api/billing/checkout`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ seller_id: activeSellerId, plan: planId }),
      });
      const checkoutData = await checkoutRes.json();
      if (!checkoutRes.ok) throw new Error(checkoutData.detail || "Unable to start checkout");

      if (checkoutData.status === "active") {
        toast.success("Plan updated.");
        await fetchSummary();
        return;
      }

      if (checkoutData.status === "manual_contact_required") {
        toast.info(checkoutData.message || "Upgrade request recorded.");
        return;
      }

      if (checkoutData.status === "checkout_required") {
        const loaded = await loadRazorpayScript();
        if (!loaded || !window.Razorpay) {
          toast.error("Failed to load Razorpay checkout.");
          return;
        }

        const razorpay = new window.Razorpay({
          key: checkoutData.key_id,
          order_id: checkoutData.order_id,
          amount: checkoutData.amount,
          currency: checkoutData.currency,
          name: checkoutData.name,
          description: checkoutData.description,
          handler: async (response: Record<string, string>) => {
            const confirmRes = await fetch(`${API_URL}/api/billing/confirm`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
              },
              body: JSON.stringify({
                seller_id: activeSellerId,
                plan: planId,
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
              }),
            });
            const confirmData = await confirmRes.json();
            if (!confirmRes.ok) {
              throw new Error(confirmData.detail || "Payment verification failed");
            }
            toast.success(`${planId.toUpperCase()} plan activated.`);
            await fetchSummary();
          },
          theme: { color: "#10b981" },
        });

        razorpay.open();
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Billing action failed.";
      toast.error(message);
    } finally {
      setActionPlan("");
    }
  };

  if (authLoading || loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-emerald-400" />
      </div>
    );
  }

  if (!summary) {
    return null;
  }

  return (
    <div className="mx-auto max-w-6xl p-4 md:p-8">
      <Toaster theme="dark" position="top-center" />

      <header className="mb-8 flex flex-col items-start justify-between gap-4 border-b border-[var(--border)] py-6 sm:flex-row sm:items-center">
        <div>
          <Link
            href="/dashboard"
            className="mb-4 inline-flex items-center gap-2 text-sm font-medium text-[var(--text-muted)] transition-colors hover:text-[var(--text-primary)]"
          >
            <ArrowLeft className="h-4 w-4" />
            Dashboard
          </Link>
          <h1 className="text-3xl font-extrabold tracking-tight text-[var(--text-primary)]">Billing and Plans</h1>
          <p className="mt-2 text-[var(--text-secondary)]">
            Track usage, compare plans, and upgrade when your seller workflow outgrows the free tier.
          </p>
        </div>
        <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-400">
          Current plan: <span className="font-bold uppercase">{summary.current_plan}</span>
        </div>
      </header>

      <div className="mb-8 grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--card-bg)] p-6 shadow-xl">
          <div className="mb-3 flex items-center gap-2 text-[var(--text-primary)]">
            <Wallet className="h-5 w-5 text-emerald-400" />
            <h2 className="text-lg font-bold">Product usage</h2>
          </div>
          <p className="text-3xl font-extrabold text-[var(--text-primary)]">{summary.usage.products.used}</p>
          <p className="mt-2 text-sm text-[var(--text-secondary)]">
            {summary.usage.products.limit === null
              ? "Unlimited on your current plan"
              : `${summary.usage.products.remaining} of ${summary.usage.products.limit} products remaining`}
          </p>
        </div>

        <div className="rounded-2xl border border-[var(--border)] bg-[var(--card-bg)] p-6 shadow-xl">
          <div className="mb-3 flex items-center gap-2 text-[var(--text-primary)]">
            <MessageCircleMore className="h-5 w-5 text-cyan-400" />
            <h2 className="text-lg font-bold">WhatsApp usage</h2>
          </div>
          <p className="text-3xl font-extrabold text-[var(--text-primary)]">{summary.usage.whatsapp_messages.used}</p>
          <p className="mt-2 text-sm text-[var(--text-secondary)]">
            {summary.usage.whatsapp_messages.limit === null
              ? "Unlimited on your current plan"
              : `${summary.usage.whatsapp_messages.remaining} of ${summary.usage.whatsapp_messages.limit} messages remaining this month`}
          </p>
          <p className="mt-2 text-xs text-[var(--text-muted)]">
            Usage period started on {summary.usage.period_start}
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {summary.plans.map((plan, index) => {
          const isCurrent = summary.current_plan === plan.id;
          const isPopular = plan.id === "pro";

          return (
            <motion.div
              key={plan.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.08 }}
              className={`rounded-3xl border p-6 shadow-2xl ${
                isPopular
                  ? "border-emerald-500/30 bg-emerald-500/5"
                  : "border-[var(--border)] bg-[var(--card-bg)]"
              }`}
            >
              <div className="mb-6 flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-bold text-[var(--text-primary)]">{plan.name}</h2>
                  <p className="mt-2 text-sm text-[var(--text-secondary)]">{plan.description}</p>
                </div>
                {isPopular && (
                  <div className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400">
                    Popular
                  </div>
                )}
              </div>

              <div className="mb-6">
                <p className="text-4xl font-extrabold text-[var(--text-primary)]">
                  {plan.price_inr === 0 ? "₹0" : `₹${plan.price_inr}`}
                  <span className="ml-1 text-base font-medium text-[var(--text-muted)]">/{plan.interval}</span>
                </p>
              </div>

              <ul className="mb-6 space-y-3">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm text-[var(--text-secondary)]">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              <button
                type="button"
                disabled={isCurrent || actionPlan === plan.id}
                onClick={() => handlePlanAction(plan.id)}
                className={`w-full rounded-xl px-4 py-3 text-sm font-semibold transition-all ${
                  isCurrent
                    ? "cursor-default border border-[var(--border)] bg-[var(--bg-primary)] text-[var(--text-muted)]"
                    : isPopular
                      ? "bg-gradient-to-r from-emerald-500 to-teal-600 text-white hover:from-emerald-400 hover:to-teal-500"
                      : "border border-[var(--border)] bg-[var(--bg-primary)] text-[var(--text-primary)] hover:bg-[var(--card-hover)]"
                }`}
              >
                {isCurrent ? "Current plan" : actionPlan === plan.id ? "Processing..." : `Choose ${plan.name}`}
              </button>

              {plan.id === "enterprise" && (
                <p className="mt-3 text-xs text-[var(--text-muted)]">
                  Enterprise also covers multi-store workflows, API access, custom branding, and ONDC rollout support.
                </p>
              )}
            </motion.div>
          );
        })}
      </div>

      <div className="mt-8 rounded-3xl border border-[var(--border)] bg-[var(--card-bg)] p-6 text-sm text-[var(--text-secondary)]">
        <div className="mb-2 flex items-center gap-2 text-[var(--text-primary)]">
          <Crown className="h-4 w-4 text-amber-400" />
          <span className="font-semibold">What monetization is enforcing right now</span>
        </div>
        <p>
          Free tier is capped at 100 products and 100 WhatsApp messages per month. Voice notes and image
          recognition unlock on Pro and Enterprise. Billing activity and plan changes are tracked in the
          backend for seller-level usage management.
        </p>
      </div>
    </div>
  );
}
