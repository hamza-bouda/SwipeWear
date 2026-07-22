"use client";

import { motion } from "framer-motion";

const steps = [
  {
    num: "01",
    title: "Swipe",
    description: "Fais defiler les pieces comme sur une app de dating. Like a droite, passe a gauche.",
    icon: (
      <svg viewBox="0 0 48 48" className="w-10 h-10" fill="none" stroke="currentColor" strokeWidth="1.5">
        <rect x="8" y="6" width="32" height="36" rx="4" className="text-violet-400" />
        <path d="M24 28l6-6M24 28l-6-6" className="text-violet-300" strokeLinecap="round" />
        <path d="M36 20l8 4-8 4" className="text-emerald-400" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    gradient: "from-violet-600/20 to-violet-400/5",
    border: "border-violet-500/20",
  },
  {
    num: "02",
    title: "L'IA apprend",
    description: "A chaque swipe, l'algorithme comprend mieux ton style. Plus tu swipes, plus il est precis.",
    icon: (
      <svg viewBox="0 0 48 48" className="w-10 h-10" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="24" cy="24" r="16" className="text-purple-400" />
        <path d="M16 24c0-4 3-8 8-8s8 4 8 8-3 8-8 8" className="text-purple-300" strokeLinecap="round" />
        <circle cx="24" cy="24" r="3" className="text-purple-200" fill="currentColor" />
      </svg>
    ),
    gradient: "from-purple-600/20 to-purple-400/5",
    border: "border-purple-500/20",
  },
  {
    num: "03",
    title: "Trouve le meilleur prix",
    description: "Tu likes une piece ? On la cherche partout et on te montre l'echelle de prix, du moins cher au plus cher.",
    icon: (
      <svg viewBox="0 0 48 48" className="w-10 h-10" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M8 36l10-10 8 6 14-18" className="text-emerald-400" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="36" cy="12" r="4" className="text-emerald-300" />
        <path d="M6 40h36" className="text-emerald-400/50" strokeLinecap="round" />
      </svg>
    ),
    gradient: "from-emerald-600/20 to-emerald-400/5",
    border: "border-emerald-500/20",
  },
];

const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.2 },
  },
};

const cardVariants = {
  hidden: { opacity: 0, y: 40 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] },
  },
};

export function HowItWorks() {
  return (
    <section id="comment-ca-marche" className="relative py-24 sm:py-32 px-4">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-violet-950/5 to-transparent pointer-events-none" />

      <div className="relative max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <span className="inline-block text-xs font-mono tracking-widest text-violet-400 uppercase mb-4">
            Comment ca marche
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold">
            Trois etapes.{" "}
            <span className="bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
              Zero prise de tete.
            </span>
          </h2>
        </motion.div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          className="grid md:grid-cols-3 gap-6"
        >
          {steps.map((step) => (
            <motion.div
              key={step.num}
              variants={cardVariants}
              whileHover={{ y: -8, transition: { duration: 0.3 } }}
              className={`group relative rounded-2xl bg-gradient-to-b ${step.gradient} border ${step.border} p-8 transition-colors duration-300 hover:border-white/10`}
            >
              <div className="flex items-start justify-between mb-6">
                <div className="p-3 rounded-xl bg-white/5 group-hover:bg-white/10 transition-colors">
                  {step.icon}
                </div>
                <span className="text-4xl font-black text-white/[0.04] group-hover:text-white/[0.08] transition-colors">
                  {step.num}
                </span>
              </div>
              <h3 className="text-xl font-bold mb-3">{step.title}</h3>
              <p className="text-sm text-white/50 leading-relaxed">
                {step.description}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
