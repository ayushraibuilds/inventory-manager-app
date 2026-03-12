import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Shield } from "lucide-react";

export const metadata: Metadata = {
  title: "Privacy Policy | ONDC Super Seller",
  description:
    "Privacy policy for ONDC Super Seller, a WhatsApp-first inventory management product for sellers.",
};

const sections = [
  {
    title: "What we collect",
    body:
      "We collect account details such as seller name, phone number, and profile information. We also process inventory messages, voice notes, images, product records, activity logs, and order-related metadata needed to operate the service.",
  },
  {
    title: "How we use the data",
    body:
      "We use this data to maintain seller inventory, process WhatsApp updates, provide dashboard visibility, generate alerts, improve parsing quality, and support core operations such as imports, exports, and catalog history.",
  },
  {
    title: "Third-party services",
    body:
      "The product relies on third-party providers including Twilio for WhatsApp delivery, Supabase for database and auth services, and Groq or similar AI providers for message understanding. Those providers may process data strictly to deliver the product workflow.",
  },
  {
    title: "Data retention",
    body:
      "We retain account, catalog, and activity data while a seller workspace is active and for a limited period afterward where required for security, auditability, backups, or legal compliance. Sellers can request deletion subject to those obligations.",
  },
  {
    title: "Security",
    body:
      "We use authentication, transport security, request validation, and operational safeguards to protect seller data. No system is perfect, so sellers should avoid sending unnecessary personal or highly sensitive data through the product.",
  },
  {
    title: "Contact",
    body:
      "For privacy requests, deletion requests, or security concerns, contact the operator of the deployed ONDC Super Seller instance through the support channel listed on the seller dashboard or onboarding flow.",
  },
];

export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-[var(--bg-primary)]">
      <div className="mx-auto max-w-4xl px-6 py-16">
        <Link
          href="/"
          className="mb-8 inline-flex items-center gap-2 text-sm font-medium text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to home
        </Link>

        <div className="rounded-3xl border border-[var(--border)] bg-[var(--card-bg)] p-8 md:p-10 shadow-sm">
          <div className="mb-8 flex items-start gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-500">
              <Shield className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.22em] text-emerald-500">Privacy Policy</p>
              <h1 className="mt-2 text-3xl font-bold text-[var(--text-primary)] md:text-4xl">How seller data is handled</h1>
              <p className="mt-3 text-[var(--text-secondary)]">
                ONDC Super Seller is built to help sellers maintain inventory over WhatsApp and the dashboard.
                This page explains the baseline data-handling expectations for the product.
              </p>
            </div>
          </div>

          <div className="space-y-8">
            {sections.map((section) => (
              <section key={section.title}>
                <h2 className="text-xl font-semibold text-[var(--text-primary)]">{section.title}</h2>
                <p className="mt-2 leading-7 text-[var(--text-secondary)]">{section.body}</p>
              </section>
            ))}
          </div>

          <div className="mt-10 rounded-2xl border border-[var(--border)] bg-[var(--bg-primary)] p-5 text-sm text-[var(--text-secondary)]">
            Last updated: March 13, 2026
          </div>
        </div>
      </div>
    </main>
  );
}
