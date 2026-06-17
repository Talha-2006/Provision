import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Provision | Canadian Startup Compliance",
  description:
    "Citation-grounded compliance research for Canadian startup founders.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
