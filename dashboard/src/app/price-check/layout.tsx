import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Price Intelligence — ONDC Super Seller",
    description:
        "Compare your catalog prices against market averages. See which products are competitively priced and where you can improve.",
};

export default function PriceCheckLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return children;
}
