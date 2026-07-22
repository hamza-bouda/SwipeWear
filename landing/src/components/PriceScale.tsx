"use client";

import { motion } from "framer-motion";

const prices = [
  { platform: "Vinted", price: "15 €", condition: "Bon etat", best: true },
  { platform: "eBay", price: "22 €", condition: "Tres bon etat", best: false },
  { platform: "Vestiaire Co.", price: "38 €", condition: "Comme neuf", best: false },
  { platform: "Zalando 2nd", price: "45 €", condition: "Neuf avec etiquette", best: false },
];

const barVariants = {
  hidden: { width: 0, opacity: 0 },
  visible: (i: number) => ({
    width: `${40 + i * 20}%`,
    opacity: 1,
    transition: { duration: 0.8, delay: i * 0.15, ease: [0.16, 1, 0.3, 1] },
  }),
};

export function PriceScale() {
  return (
    <section className="relative py-24 sm:py-32 px-4">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-purple-950/5 to-transparent pointer-events-none" />

      <div className="relative max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <span className="inline-block text-xs font-mono tracking-widest text-emerald-400 uppercase mb-4">
            Echelle de prix
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold">
            Tu likes une piece ?{" "}
            <span className="bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">
              On te trouve le meilleur prix.
            </span>
          </h2>
          <p className="mt-4 text-white/40 max-w-xl mx-auto">
            SwipeWear cherche la meme piece sur toutes les plateformes et te montre ou elle est la moins chere.
          </p>
        </motion.div>

        {/* Price ladder card */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ duration: 0.7 }}
          className="glass rounded-2xl p-6 sm:p-8"
        >
          {/* Item header */}
          <div className="flex items-center gap-4 mb-8 pb-6 border-b border-white/5">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-violet-600/30 to-purple-500/20 flex items-center justify-center">
              <svg viewBox="0 0 24 24" className="w-7 h-7 text-violet-400" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M2 18l4-4 4 4 8-12 4 4" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <div>
              <p className="font-bold text-lg">Nike Air Max 90</p>
              <p className="text-sm text-white/40">Taille 42 &middot; Coloris blanc/noir</p>
            </div>
          </div>

          {/* Price bars */}
          <div className="space-y-4">
            {prices.map((item, i) => (
              <motion.div
                key={item.platform}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                custom={i}
                className="group"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{item.platform}</span>
                    {item.best && (
                      <span className="text-[10px] font-semibold bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full">
                        MEILLEUR PRIX
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-white/30">{item.condition}</span>
                    <span className={`text-sm font-bold ${item.best ? "text-emerald-400" : "text-white/70"}`}>
                      {item.price}
                    </span>
                  </div>
                </div>
                <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                  <motion.div
                    variants={barVariants}
                    custom={i}
                    className={`h-full rounded-full ${
                      item.best
                        ? "bg-gradient-to-r from-emerald-500 to-emerald-400"
                        : "bg-gradient-to-r from-white/10 to-white/20"
                    }`}
                  />
                </div>
              </motion.div>
            ))}
          </div>

          {/* CTA */}
          <div className="mt-8 pt-6 border-t border-white/5 flex items-center justify-between">
            <p className="text-sm text-white/30">
              Economie potentielle : <span className="text-emerald-400 font-semibold">30 &euro;</span>
            </p>
            <div className="text-xs text-white/20 font-mono">
              4 sources comparees
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
