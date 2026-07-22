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
      {/* ─── Background grid ─── */}
      <div
        className="pointer-events-none fixed inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      {/* ─── Hero radial glow ─── */}
      <div className="pointer-events-none absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-gradient-radial from-violet-600/8 to-transparent rounded-full blur-3xl" />

      {/* ─── Navbar ─── */}
      <nav className="fixed top-0 inset-x-0 z-50 glass">
        <div className="max-w-5xl mx-auto flex items-center justify-between px-4 py-3">
          <span className="text-lg font-bold bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
            SwipeWear
          </span>
          <div className="hidden sm:flex items-center gap-6 text-sm text-white/50">
            <a href="#comment-ca-marche" className="hover:text-white transition-colors">
              Comment ca marche
            </a>
            <a href="#faq" className="hover:text-white transition-colors">
              FAQ
            </a>
          </div>
          <a
            href="#waitlist"
            className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500 transition-colors"
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
              <div className="inline-flex items-center gap-2 rounded-full bg-violet-500/10 border border-violet-500/20 px-4 py-1.5 mb-6">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-violet-500" />
                </span>
                <span className="text-xs font-medium text-violet-300">
                  Bientot disponible
                </span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black leading-[1.1] tracking-tight">
                L&apos;IA qui{" "}
                <span className="bg-gradient-to-r from-violet-400 via-purple-400 to-fuchsia-400 bg-clip-text text-transparent animate-gradient">
                  snipe les pepites
                </span>{" "}
                de la seconde main
              </h1>

              <p className="mt-6 text-lg text-white/40 leading-relaxed max-w-lg">
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
              className="mt-8 flex items-center gap-4"
            >
              <div className="flex -space-x-2">
                {[
                  "bg-gradient-to-br from-violet-400 to-purple-600",
                  "bg-gradient-to-br from-emerald-400 to-teal-600",
                  "bg-gradient-to-br from-amber-400 to-orange-600",
                  "bg-gradient-to-br from-pink-400 to-rose-600",
                ].map((bg, i) => (
                  <div
                    key={i}
                    className={`w-8 h-8 rounded-full ${bg} border-2 border-[#050505] flex items-center justify-center text-[10px] font-bold text-white`}
                  >
                    {String.fromCharCode(65 + i)}
                  </div>
                ))}
              </div>
              <p className="text-xs text-white/30">
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
            className="w-5 h-8 rounded-full border border-white/10 flex items-start justify-center pt-1.5"
          >
            <div className="w-1 h-2 rounded-full bg-white/20" />
          </motion.div>
        </motion.div>
      </section>

      {/* ─── Sections ─── */}
      <HowItWorks />
      <PriceScale />

      {/* ─── CTA band ─── */}
      <section className="relative py-24 px-4">
        <div className="absolute inset-0 bg-gradient-to-r from-violet-600/5 via-purple-600/10 to-violet-600/5 pointer-events-none" />
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="relative max-w-xl mx-auto text-center"
        >
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            Pret a decouvrir tes futures pepites ?
          </h2>
          <p className="text-white/40 mb-8">
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
