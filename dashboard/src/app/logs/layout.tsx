import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Activity Logs — ONDC Super Seller",
    description: "View recent WhatsApp interactions and catalog activity for your seller account.",
};

export default function LogsLayout({ children }: { children: React.ReactNode }) {
    return children;
}
