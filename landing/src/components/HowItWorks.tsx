"use client";

import { motion } from "framer-motion";

const steps = [
  {
    num: "01",
    title: "Swipe",
    description: "Fais defiler les pieces comme sur une app de dating. Like a droite, passe a gauche.",
    icon: (
      <svg viewBox="0 0 48 48" className="w-10 h-10" fill="none" stroke="currentColor" strokeWidth="1.5">
        <rect x="8" y="6" width="32" height="36" rx="4" className="text-black/20" />
        <path d="M24 28l6-6M24 28l-6-6" className="text-black/40" strokeLinecap="round" />
        <path d="M36 20l8 4-8 4" className="text-yellow-500" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    num: "02",
    title: "L'IA apprend",
    description: "A chaque swipe, l'algorithme comprend mieux ton style. Plus tu swipes, plus il est precis.",
    icon: (
      <svg viewBox="0 0 48 48" className="w-10 h-10" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="24" cy="24" r="16" className="text-black/15" />
        <path d="M16 24c0-4 3-8 8-8s8 4 8 8-3 8-8 8" className="text-black/30" strokeLinecap="round" />
        <circle cx="24" cy="24" r="3" className="text-yellow-500" fill="currentColor" />
      </svg>
    ),
  },
  {
    num: "03",
    title: "Meilleur prix",
    description: "Tu likes une piece ? On la cherche partout et on te montre l'echelle de prix, du moins cher au plus cher.",
    icon: (
      <svg viewBox="0 0 48 48" className="w-10 h-10" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M8 36l10-10 8 6 14-18" className="text-yellow-500" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="36" cy="12" r="4" className="text-yellow-500" />
        <path d="M6 40h36" className="text-black/10" strokeLinecap="round" />
      </svg>
    ),
  },
];

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.15 } },
};

const cardVariants = {
  hidden: { opacity: 0, y: 40 },
  visible: {
    opacity: 1, y: 0,
    transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] },
  },
};

export function HowItWorks() {
  return (
    <section id="comment-ca-marche" className="relative py-24 sm:py-32 px-4 bg-neutral-50">
      <div className="relative max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <span className="inline-block text-[11px] font-mono tracking-[0.2em] text-yellow-600 uppercase mb-4">
            Comment ca marche
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-black">
            Trois etapes.{" "}
            <span className="relative">
              <span className="relative z-10">Zero prise de tete.</span>
              <span className="absolute bottom-1 left-0 right-0 h-3 bg-yellow-400/30 -z-0 rounded-sm" />
            </span>
          </h2>
        </motion.div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          className="grid md:grid-cols-3 gap-5"
        >
          {steps.map((step) => (
            <motion.div
              key={step.num}
              variants={cardVariants}
              whileHover={{ y: -6, transition: { duration: 0.3 } }}
              className="group relative rounded-2xl border border-black/[0.04] bg-white p-8 transition-all duration-300 hover:shadow-lg hover:shadow-black/[0.03] hover:border-yellow-400/20"
            >
              <div className="flex items-start justify-between mb-6">
                <div className="p-3 rounded-xl bg-neutral-50 group-hover:bg-yellow-50 transition-colors">
                  {step.icon}
                </div>
                <span className="text-5xl font-black text-black/[0.03] group-hover:text-yellow-400/20 transition-colors select-none">
                  {step.num}
                </span>
              </div>
              <h3 className="text-xl font-bold mb-3 text-black group-hover:text-yellow-600 transition-colors">{step.title}</h3>
              <p className="text-sm text-black/40 leading-relaxed">
                {step.description}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
