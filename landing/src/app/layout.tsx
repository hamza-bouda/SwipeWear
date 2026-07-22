import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "SwipeWear — L'IA qui snipe les pepites de la seconde main",
  description:
    "Swipe, like, trouve. SwipeWear utilise l'intelligence artificielle pour dénicher les meilleures affaires mode de seconde main. Inscris-toi à la waitlist.",
  keywords: [
    "seconde main",
    "mode",
    "IA",
    "vinted",
    "occasion",
    "sneakers",
    "streetwear",
    "swipe",
    "fashion",
  ],
  openGraph: {
    title: "SwipeWear — L'IA qui snipe les pepites de la seconde main",
    description:
      "Swipe, like, trouve. L'app qui apprend ton style et te snipe les meilleures affaires mode d'occasion.",
    type: "website",
    locale: "fr_FR",
  },
  twitter: {
    card: "summary_large_image",
    title: "SwipeWear — L'IA qui snipe les pepites",
    description:
      "L'app qui apprend ton style et te snipe les meilleures affaires mode d'occasion.",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="fr"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
