import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "GovScheme AI — Discover Government Schemes for You",
  description:
    "AI-powered platform to discover, check eligibility, and apply for 3,400+ government schemes across India. Personalized recommendations in 10 languages.",
  keywords: [
    "government schemes",
    "India",
    "eligibility",
    "scholarships",
    "farmer schemes",
    "AI recommendations",
  ],
};

import { LanguageProvider } from "@/context/LanguageContext";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.ico" />
        <meta name="theme-color" content="#1a365d" />
      </head>
      <body className={`${inter.variable} font-sans antialiased`}>
        <LanguageProvider>{children}</LanguageProvider>
      </body>
    </html>
  );
}
