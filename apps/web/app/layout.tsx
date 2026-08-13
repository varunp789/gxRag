import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "gxRag Platform",
  description: "Graph RAG monorepo foundation with client and admin portals.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

