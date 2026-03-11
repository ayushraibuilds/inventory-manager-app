import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/components/AuthProvider";

export const metadata: Metadata = {
  title: "ONDC Super Seller — WhatsApp Inventory Dashboard",
  description:
    "Manage your ONDC catalog through WhatsApp voice notes, images, and text. Real-time dashboard with analytics, price intelligence, and order management.",
  keywords: ["ONDC", "WhatsApp", "inventory", "catalog", "kirana", "India", "seller"],
  openGraph: {
    title: "ONDC Super Seller",
    description:
      "Let Indian shopkeepers manage their ONDC catalog through WhatsApp — in Hindi, English, or Hinglish.",
    type: "website",
    locale: "en_IN",
  },
  twitter: {
    card: "summary_large_image",
    title: "ONDC Super Seller",
    description:
      "WhatsApp-native inventory management for ONDC. Voice, image, and text support.",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#58a6ff" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        {/* eslint-disable-next-line @next/next/no-page-custom-font */}
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet" />
      </head>
      <body suppressHydrationWarning>
        <AuthProvider>
          {children}
          <script
            dangerouslySetInnerHTML={{
              __html: `
              if ('serviceWorker' in navigator) {
                navigator.serviceWorker.getRegistrations().then(function(regs) {
                  regs.forEach(function(r) { r.unregister(); });
                });
                caches.keys().then(function(keys) {
                  keys.forEach(function(k) { caches.delete(k); });
                });
              }
            `
            }}
          />
        </AuthProvider>
      </body>
    </html>
  );
}
