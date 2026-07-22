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
      <div className="relative max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <span className="inline-block text-[11px] font-mono tracking-[0.2em] text-black/30 uppercase mb-4">
            Echelle de prix
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-black">
            Tu likes une piece ?{" "}
            <span className="relative">
              <span className="relative z-10">On te trouve le meilleur prix.</span>
              <span className="absolute bottom-1 left-0 right-0 h-3 bg-yellow-400/30 -z-0 rounded-sm" />
            </span>
          </h2>
          <p className="mt-4 text-black/35 max-w-xl mx-auto">
            SwipeWear cherche la meme piece sur toutes les plateformes et te montre ou elle est la moins chere.
          </p>
        </motion.div>

        {/* Price ladder card */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ duration: 0.7 }}
          className="rounded-2xl border border-black/[0.06] bg-white p-6 sm:p-8 shadow-sm"
        >
          {/* Item header */}
          <div className="flex items-center gap-4 mb-8 pb-6 border-b border-black/[0.04]">
            <div className="w-14 h-14 rounded-xl bg-yellow-50 border border-yellow-200/50 flex items-center justify-center">
              <svg viewBox="0 0 24 24" className="w-7 h-7 text-yellow-500" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M2 18l4-4 4 4 8-12 4 4" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <div>
              <p className="font-bold text-lg text-black">Nike Air Max 90</p>
              <p className="text-sm text-black/35">Taille 42 &middot; Coloris blanc/noir</p>
            </div>
          </div>

          {/* Price bars */}
          <div className="space-y-5">
            {prices.map((item, i) => (
              <motion.div
                key={item.platform}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                custom={i}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-black">{item.platform}</span>
                    {item.best && (
                      <span className="text-[10px] font-bold bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full uppercase tracking-wider">
                        Meilleur prix
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-black/25">{item.condition}</span>
                    <span className={`text-sm font-bold tabular-nums ${item.best ? "text-yellow-600" : "text-black/50"}`}>
                      {item.price}
                    </span>
                  </div>
                </div>
                <div className="h-2 rounded-full bg-black/[0.03] overflow-hidden">
                  <motion.div
                    variants={barVariants}
                    custom={i}
                    className={`h-full rounded-full ${
                      item.best
                        ? "bg-yellow-400"
                        : "bg-black/[0.06]"
                    }`}
                  />
                </div>
              </motion.div>
            ))}
          </div>

          {/* Footer */}
          <div className="mt-8 pt-6 border-t border-black/[0.04] flex items-center justify-between">
            <p className="text-sm text-black/30">
              Economie potentielle : <span className="text-yellow-600 font-semibold">30 &euro;</span>
            </p>
            <div className="text-xs text-black/15 font-mono tracking-wider">
              4 sources comparees
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
