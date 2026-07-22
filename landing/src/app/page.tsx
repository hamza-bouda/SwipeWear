"use client";

import { motion } from "framer-motion";
import { WaitlistForm } from "@/components/WaitlistForm";
import { PhoneMockup } from "@/components/PhoneMockup";
import { HowItWorks } from "@/components/HowItWorks";
import { PriceScale } from "@/components/PriceScale";
import { FAQ } from "@/components/FAQ";
import { Footer } from "@/components/Footer";

export default function Home() {
  return (
    <main className="relative">
      {/* ─── Subtle grid ─── */}
      <div
        className="pointer-events-none fixed inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(0,0,0,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,0.05) 1px, transparent 1px)",
          backgroundSize: "80px 80px",
        }}
      />

      {/* ─── Hero glow ─── */}
      <div className="pointer-events-none absolute -top-32 left-1/2 -translate-x-1/2 w-[600px] h-[500px] bg-yellow-400/[0.06] rounded-full blur-[120px]" />

      {/* ─── Navbar ─── */}
      <nav className="fixed top-0 inset-x-0 z-50 glass">
        <div className="max-w-5xl mx-auto flex items-center justify-between px-4 sm:px-6 py-3.5">
          <span className="text-lg font-black tracking-tight">
            Swipe<span className="text-yellow-500">Wear</span>
          </span>
          <div className="hidden sm:flex items-center gap-8 text-sm text-black/40">
            <a href="#comment-ca-marche" className="hover:text-black/80 transition-colors">
              Comment ca marche
            </a>
            <a href="#faq" className="hover:text-black/80 transition-colors">
              FAQ
            </a>
          </div>
          <a
            href="#waitlist"
            className="rounded-full bg-black px-5 py-2 text-sm font-bold text-white hover:bg-black/80 transition-colors"
          >
            Rejoindre
          </a>
        </div>
      </nav>

      {/* ─── Hero ─── */}
      <section className="relative min-h-screen flex items-center pt-20 pb-16 px-4">
        <div className="max-w-5xl mx-auto w-full grid lg:grid-cols-2 gap-12 lg:gap-8 items-center">
          {/* Left: copy + form */}
          <div className="order-2 lg:order-1">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
            >
              <div className="inline-flex items-center gap-2 rounded-full bg-yellow-400/10 border border-yellow-400/20 px-4 py-1.5 mb-6">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-500 opacity-75" />
                  <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-yellow-500" />
                </span>
                <span className="text-xs font-semibold text-yellow-600">
                  Bientot disponible
                </span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-[3.5rem] font-black leading-[1.08] tracking-tight text-black">
                L&apos;IA qui{" "}
                <span className="relative">
                  <span className="relative z-10">snipe les pepites</span>
                  <span className="absolute bottom-1 left-0 right-0 h-3 bg-yellow-400/40 -z-0 rounded-sm" />
                </span>
                <br />
                de la seconde main
              </h1>

              <p className="mt-6 text-base sm:text-lg text-black/40 leading-relaxed max-w-md">
                Swipe, like, trouve. SwipeWear apprend ton style et te deniche
                les meilleures affaires mode d&apos;occasion — au meilleur prix.
              </p>
            </motion.div>

            <motion.div
              id="waitlist"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
              className="mt-8"
            >
              <WaitlistForm />
            </motion.div>

            {/* Social proof */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5, duration: 0.6 }}
              className="mt-8 flex items-center gap-3"
            >
              <div className="flex -space-x-2">
                {["#facc15", "#0a0a0a", "#a3a3a3", "#fde047"].map((color, i) => (
                  <div
                    key={i}
                    className="w-7 h-7 rounded-full border-2 border-white flex items-center justify-center text-[9px] font-bold shadow-sm"
                    style={{ background: color, color: color === "#0a0a0a" || color === "#a3a3a3" ? "#fff" : "#000" }}
                  >
                    {String.fromCharCode(65 + i)}
                  </div>
                ))}
              </div>
              <p className="text-xs text-black/30">
                Rejoins les premiers a tester SwipeWear
              </p>
            </motion.div>
          </div>

          {/* Right: phone mockup */}
          <div className="order-1 lg:order-2 flex justify-center">
            <PhoneMockup />
          </div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 hidden lg:block"
        >
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="w-5 h-8 rounded-full border border-black/10 flex items-start justify-center pt-1.5"
          >
            <div className="w-1 h-2 rounded-full bg-yellow-500/50" />
          </motion.div>
        </motion.div>
      </section>

      {/* ─── Sections ─── */}
      <HowItWorks />
      <PriceScale />

      {/* ─── CTA band ─── */}
      <section className="relative py-24 px-4">
        <div className="absolute inset-0 bg-gradient-to-b from-yellow-50/50 via-yellow-50 to-yellow-50/50 pointer-events-none" />
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="relative max-w-xl mx-auto text-center"
        >
          <h2 className="text-3xl sm:text-4xl font-bold mb-4 text-black">
            Pret a decouvrir tes{" "}
            <span className="relative">
              <span className="relative z-10">futures pepites</span>
              <span className="absolute bottom-1 left-0 right-0 h-3 bg-yellow-400/40 -z-0 rounded-sm" />
            </span>{" "}?
          </h2>
          <p className="text-black/40 mb-8">
            Inscris-toi maintenant et sois parmi les premiers a tester SwipeWear.
          </p>
          <WaitlistForm />
        </motion.div>
      </section>

      <FAQ />
      <Footer />
    </main>
  );
}
