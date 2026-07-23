"use client";

import { motion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";

const steps = [
  {
    num: "01",
    title: "Swipe",
    description: "Fais defiler les pieces comme sur une app de dating. Like a droite, passe a gauche. Simple, rapide, addictif.",
    gradient: "from-yellow-400/20 to-amber-400/10",
    icon: (
      <svg viewBox="0 0 48 48" className="w-12 h-12" fill="none" stroke="currentColor" strokeWidth="1.5">
        <rect x="8" y="6" width="32" height="36" rx="4" className="text-black/10" />
        <path d="M24 28l6-6M24 28l-6-6" className="text-black/30" strokeLinecap="round" />
        <path d="M36 20l8 4-8 4" className="text-yellow-500" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
      </svg>
    ),
  },
  {
    num: "02",
    title: "L'IA apprend",
    description: "A chaque swipe, l'algorithme comprend mieux ton style, tes marques, tes tailles. Plus tu swipes, plus il est precis.",
    gradient: "from-neutral-100 to-neutral-50",
    icon: (
      <svg viewBox="0 0 48 48" className="w-12 h-12" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="24" cy="24" r="16" className="text-black/10" />
        <path d="M16 24c0-4 3-8 8-8s8 4 8 8-3 8-8 8" className="text-black/20" strokeLinecap="round" />
        <circle cx="24" cy="24" r="3" className="text-yellow-500" fill="currentColor" />
        <path d="M24 21v-6M27 24h6M24 27v6M21 24h-6" className="text-yellow-400/40" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    num: "03",
    title: "Meilleur prix",
    description: "Tu likes une piece ? On la cherche sur toutes les plateformes et on te montre l'echelle de prix. Du moins cher au plus cher.",
    gradient: "from-yellow-400/10 to-yellow-100/20",
    icon: (
      <svg viewBox="0 0 48 48" className="w-12 h-12" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M8 36l10-10 8 6 14-18" className="text-yellow-500" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
        <circle cx="36" cy="12" r="4" className="text-yellow-500" fill="currentColor" fillOpacity="0.2" />
        <circle cx="36" cy="12" r="4" className="text-yellow-500" />
        <path d="M6 40h36" className="text-black/10" strokeLinecap="round" />
      </svg>
    ),
  },
];

export function HowItWorks() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"],
  });
  const lineHeight = useTransform(scrollYProgress, [0.1, 0.8], ["0%", "100%"]);

  return (
    <section id="comment-ca-marche" aria-labelledby="how-it-works-heading" ref={containerRef} className="relative py-28 sm:py-36 px-4 overflow-hidden">
      {/* Background blob */}
      <div className="absolute top-1/4 -right-32 w-96 h-96 bg-yellow-400/[0.04] rounded-full blur-[100px] animate-blob pointer-events-none" />

      <div className="relative max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          className="text-center mb-20"
        >
          <motion.span
            initial={{ opacity: 0, scale: 0.8 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="inline-block text-[11px] font-mono tracking-[0.3em] text-yellow-600 uppercase mb-5 bg-yellow-50 px-4 py-1.5 rounded-full border border-yellow-200/50"
          >
            Comment ca marche
          </motion.span>
          <h2 id="how-it-works-heading" className="text-3xl sm:text-4xl lg:text-[3.2rem] font-black text-black leading-tight">
            Trois etapes.{" "}
            <span className="relative inline-block">
              <span className="relative z-10">Zero prise de tete.</span>
              <motion.span
                initial={{ width: 0 }}
                whileInView={{ width: "100%" }}
                viewport={{ once: true }}
                transition={{ duration: 0.8, delay: 0.3 }}
                className="absolute bottom-1 left-0 h-3 bg-yellow-400/30 -z-0 rounded-sm"
              />
            </span>
          </h2>
        </motion.div>

        {/* Steps with connecting line */}
        <div className="relative">
          {/* Vertical progress line (desktop) */}
          <div className="hidden md:block absolute left-1/2 top-0 bottom-0 w-px bg-black/[0.04]">
            <motion.div
              style={{ height: lineHeight }}
              className="w-full bg-gradient-to-b from-yellow-400 to-yellow-500/50 origin-top"
            />
          </div>

          <div className="space-y-8 md:space-y-0">
            {steps.map((step, i) => (
              <motion.div
                key={step.num}
                initial={{ opacity: 0, x: i % 2 === 0 ? -50 : 50 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-80px" }}
                transition={{ duration: 0.7, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
                className={`relative md:grid md:grid-cols-2 md:gap-16 md:py-16 ${
                  i % 2 === 0 ? "" : "md:direction-rtl"
                }`}
              >
                {/* Step dot on line */}
                <div className="hidden md:block absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
                  <motion.div
                    initial={{ scale: 0 }}
                    whileInView={{ scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.4, delay: 0.3 }}
                    className="w-4 h-4 rounded-full bg-yellow-400 border-4 border-white shadow-md"
                  />
                </div>

                <div className={`${i % 2 === 0 ? "md:text-right md:pr-16" : "md:col-start-2 md:pl-16"}`}>
                  <motion.div
                    whileHover={{ y: -4, transition: { duration: 0.3 } }}
                    className={`group relative rounded-2xl bg-gradient-to-br ${step.gradient} p-8 border border-black/[0.04] hover:border-yellow-400/20 transition-all duration-500 hover:shadow-xl hover:shadow-yellow-500/[0.03]`}
                  >
                    <div className={`flex items-start gap-5 ${i % 2 === 0 ? "md:flex-row-reverse md:text-left" : ""}`}>
                      <div className="shrink-0 p-3 rounded-2xl bg-white/80 shadow-sm group-hover:shadow-md transition-shadow">
                        {step.icon}
                      </div>
                      <div>
                        <span className="text-6xl font-black text-black/[0.04] group-hover:text-yellow-400/20 transition-colors select-none leading-none">
                          {step.num}
                        </span>
                        <h3 className="text-xl font-bold text-black group-hover:text-yellow-600 transition-colors mt-1 mb-2">
                          {step.title}
                        </h3>
                        <p className="text-sm text-black/40 leading-relaxed">
                          {step.description}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                </div>

                {i % 2 === 0 && <div className="hidden md:block" />}
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
