import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, FileText } from "lucide-react";

export const metadata: Metadata = {
  title: "Terms of Service | ONDC Super Seller",
  description:
    "Terms of service for ONDC Super Seller, a WhatsApp-first inventory management product for sellers.",
};

const sections = [
  {
    title: "Service scope",
    body:
      "ONDC Super Seller is an inventory and catalog management product for sellers. It helps sellers add, update, review, and monitor inventory through WhatsApp messages, voice notes, images, and the dashboard interface.",
  },
  {
    title: "Seller responsibilities",
    body:
      "Sellers are responsible for the accuracy of product, pricing, quantity, and compliance information they submit. They should review AI-generated updates and dashboard records before relying on them for business operations.",
  },
  {
    title: "Acceptable use",
    body:
      "You may not use the service for unlawful, abusive, fraudulent, or harmful activity, including sending unauthorized data, attempting to bypass security controls, or uploading content you do not have the right to process.",
  },
  {
    title: "Availability and changes",
    body:
      "We may update, improve, suspend, or remove features as the product evolves. External dependencies such as Twilio, Supabase, or AI providers may affect availability, latency, or functionality.",
  },
  {
    title: "Limitation of liability",
    body:
      "The service is provided on an as-is basis. To the maximum extent permitted by law, the operator is not liable for indirect, incidental, or consequential losses arising from product use, downtime, or AI-generated inaccuracies.",
  },
  {
    title: "Termination",
    body:
      "We may suspend or terminate access if a workspace violates these terms, creates operational or legal risk, or misuses the platform. Sellers may stop using the product at any time, subject to outstanding legal or billing obligations.",
  },
];

export default function TermsPage() {
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
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-500/10 text-cyan-500">
              <FileText className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.22em] text-cyan-500">Terms of Service</p>
              <h1 className="mt-2 text-3xl font-bold text-[var(--text-primary)] md:text-4xl">Terms for using the seller inventory product</h1>
              <p className="mt-3 text-[var(--text-secondary)]">
                These terms govern access to ONDC Super Seller as a seller-facing inventory management
                tool and dashboard.
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
