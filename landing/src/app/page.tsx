"use client";

import { motion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";
import { WaitlistForm } from "@/components/WaitlistForm";
import { PhoneMockup } from "@/components/PhoneMockup";
import { BrandMarquee } from "@/components/BrandMarquee";
import { HowItWorks } from "@/components/HowItWorks";
import { Stats } from "@/components/Stats";
import { PriceScale } from "@/components/PriceScale";
import { FAQ } from "@/components/FAQ";
import { Footer } from "@/components/Footer";

const letterVariants = {
  hidden: { opacity: 0, y: 40, rotateX: -40 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    rotateX: 0,
    transition: {
      duration: 0.6,
      delay: i * 0.03,
      ease: [0.16, 1, 0.3, 1],
    },
  }),
};

function AnimatedText({ text, className }: { text: string; className?: string }) {
  return (
    <span className={className}>
      {text.split("").map((char, i) => (
        <motion.span
          key={i}
          custom={i}
          variants={letterVariants}
          initial="hidden"
          animate="visible"
          className="inline-block"
          style={{ transformOrigin: "bottom" }}
        >
          {char === " " ? " " : char}
        </motion.span>
      ))}
    </span>
  );
}

export default function Home() {
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"],
  });
  const heroOpacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);
  const heroScale = useTransform(scrollYProgress, [0, 0.5], [1, 0.95]);

  return (
    <main className="relative">
      {/* ─── Subtle grid ─── */}
      <div
        className="pointer-events-none fixed inset-0 opacity-[0.02]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(0,0,0,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,0.05) 1px, transparent 1px)",
          backgroundSize: "80px 80px",
        }}
      />

      {/* ─── Animated background blobs ─── */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-32 left-1/3 w-[500px] h-[500px] bg-yellow-400/[0.05] rounded-full blur-[120px] animate-blob" />
        <div className="absolute top-1/3 -right-32 w-[400px] h-[400px] bg-yellow-300/[0.03] rounded-full blur-[100px] animate-blob" style={{ animationDelay: "-3s" }} />
        <div className="absolute bottom-1/4 -left-32 w-[350px] h-[350px] bg-amber-400/[0.03] rounded-full blur-[100px] animate-blob" style={{ animationDelay: "-5s" }} />
      </div>

      {/* ─── Navbar ─── */}
      <nav aria-label="Navigation principale" className="fixed top-0 inset-x-0 z-50 glass">
        <div className="max-w-5xl mx-auto flex items-center justify-between px-4 sm:px-6 py-3.5">
          <motion.span
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="text-lg font-black tracking-tight"
          >
            Swipe<span className="text-yellow-500">Wear</span>
          </motion.span>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="hidden sm:flex items-center gap-8 text-sm text-black/40"
          >
            <a href="#comment-ca-marche" className="hover:text-black/80 transition-colors">
              Comment ca marche
            </a>
            <a href="#faq" className="hover:text-black/80 transition-colors">
              FAQ
            </a>
          </motion.div>
          <motion.a
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            href="#waitlist"
            className="rounded-full bg-black px-5 py-2 text-sm font-bold text-white hover:bg-black/80 transition-all hover:shadow-lg hover:shadow-black/10"
          >
            Rejoindre
          </motion.a>
        </div>
      </nav>

      {/* ─── Hero ─── */}
      <motion.section
        ref={heroRef}
        style={{ opacity: heroOpacity, scale: heroScale }}
        className="relative min-h-screen flex items-center pt-20 pb-16 px-4"
      >
        <div className="max-w-5xl mx-auto w-full grid lg:grid-cols-2 gap-12 lg:gap-8 items-center">
          {/* Left: copy + form */}
          <div className="order-2 lg:order-1">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              {/* Badge */}
              <motion.div
                initial={{ opacity: 0, y: 20, scale: 0.9 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.5, delay: 0.1 }}
                className="inline-flex items-center gap-2 rounded-full bg-yellow-400/10 border border-yellow-400/20 px-4 py-1.5 mb-6"
              >
                <span className="relative flex h-1.5 w-1.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-500 opacity-75" />
                  <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-yellow-500" />
                </span>
                <span className="text-xs font-semibold text-yellow-600">
                  Bientot disponible
                </span>
              </motion.div>

              {/* Title with letter-by-letter reveal */}
              <h1 className="text-4xl sm:text-5xl lg:text-[3.5rem] font-black leading-[1.08] tracking-tight text-black overflow-hidden">
                <AnimatedText text="L'IA qui" />
                <br />
                <span className="relative inline-block mt-1">
                  <AnimatedText text="snipe les pepites" className="relative z-10" />
                  <motion.span
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: 1 }}
                    transition={{ duration: 0.8, delay: 0.8, ease: [0.16, 1, 0.3, 1] }}
                    className="absolute bottom-1 left-0 right-0 h-3 bg-yellow-400/40 -z-0 rounded-sm origin-left"
                  />
                </span>
                <br />
                <AnimatedText text="de la seconde main" />
              </h1>

              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.6 }}
                className="mt-6 text-base sm:text-lg text-black/40 leading-relaxed max-w-md"
              >
                Swipe, like, trouve. SwipeWear apprend ton style et te deniche
                les meilleures affaires mode d&apos;occasion — au meilleur prix.
              </motion.p>
            </motion.div>

            <motion.div
              id="waitlist"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.8 }}
              className="mt-8"
            >
              <WaitlistForm />
            </motion.div>

            {/* Social proof */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1.2, duration: 0.6 }}
              className="mt-8 flex items-center gap-3"
            >
              <div className="flex -space-x-2">
                {["#facc15", "#0a0a0a", "#a3a3a3", "#fde047"].map((color, i) => (
                  <motion.div
                    key={i}
                    initial={{ scale: 0, x: -10 }}
                    animate={{ scale: 1, x: 0 }}
                    transition={{ delay: 1.3 + i * 0.1, type: "spring", stiffness: 200 }}
                    className="w-7 h-7 rounded-full border-2 border-white flex items-center justify-center text-[9px] font-bold shadow-sm"
                    style={{ background: color, color: color === "#0a0a0a" || color === "#a3a3a3" ? "#fff" : "#000" }}
                  >
                    {String.fromCharCode(65 + i)}
                  </motion.div>
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
          transition={{ delay: 2 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 hidden lg:flex flex-col items-center gap-2"
        >
          <span className="text-[10px] tracking-[0.2em] uppercase text-black/15 font-medium">Scroll</span>
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="w-5 h-8 rounded-full border border-black/10 flex items-start justify-center pt-1.5"
          >
            <div className="w-1 h-2 rounded-full bg-yellow-500/50" />
          </motion.div>
        </motion.div>
      </motion.section>

      {/* ─── Brand Marquee ─── */}
      <BrandMarquee />

      {/* ─── How It Works ─── */}
      <HowItWorks />

      {/* ─── Stats ─── */}
      <Stats />

      {/* ─── Price Scale ─── */}
      <PriceScale />

      {/* ─── CTA band ─── */}
      <section className="relative py-28 px-4 overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0 bg-gradient-to-b from-white via-yellow-50/50 to-white pointer-events-none" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-yellow-400/[0.06] rounded-full blur-[120px] pointer-events-none" />

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="relative max-w-xl mx-auto text-center"
        >
          <motion.div
            initial={{ scale: 0 }}
            whileInView={{ scale: 1 }}
            viewport={{ once: true }}
            transition={{ type: "spring", stiffness: 200, delay: 0.2 }}
            className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-yellow-50 border border-yellow-200/50 mb-6 shadow-sm"
          >
            <span className="text-3xl">&#128293;</span>
          </motion.div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black mb-4 text-black">
            Pret a decouvrir tes{" "}
            <span className="relative inline-block">
              <span className="relative z-10">futures pepites</span>
              <motion.span
                initial={{ scaleX: 0 }}
                whileInView={{ scaleX: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: 0.3 }}
                className="absolute bottom-1 left-0 right-0 h-3 bg-yellow-400/40 -z-0 rounded-sm origin-left"
              />
            </span>{" "}?
          </h2>
          <p className="text-black/40 mb-8 text-lg">
            Inscris-toi maintenant et sois parmi les premiers a tester SwipeWear.
          </p>
          <WaitlistForm />
        </motion.div>
      </section>

      {/* ─── FAQ ─── */}
      <FAQ />

      {/* ─── Footer ─── */}
      <Footer />
    </main>
  );
}
