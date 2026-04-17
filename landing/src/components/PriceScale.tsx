"use client";

import { motion } from "framer-motion";

const prices = [
  { platform: "Vinted", price: "15 €", condition: "Bon etat", best: true, width: "40%" },
  { platform: "eBay", price: "22 €", condition: "Tres bon etat", best: false, width: "55%" },
  { platform: "Vestiaire Co.", price: "38 €", condition: "Comme neuf", best: false, width: "78%" },
  { platform: "Zalando 2nd", price: "45 €", condition: "Neuf avec etiquette", best: false, width: "95%" },
];

export function PriceScale() {
  return (
    <section className="relative py-28 sm:py-36 px-4 bg-neutral-50/50">
      {/* Background accents */}
      <div className="absolute top-0 left-1/4 w-72 h-72 bg-yellow-400/[0.03] rounded-full blur-[100px] pointer-events-none" />

      <div className="relative max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.7 }}
          className="text-center mb-16"
        >
          <span className="inline-block text-[11px] font-mono tracking-[0.3em] text-black/25 uppercase mb-5 bg-black/[0.02] px-4 py-1.5 rounded-full border border-black/[0.04]">
            Echelle de prix
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-[3.2rem] font-black text-black leading-tight">
            Tu likes une piece ?{" "}
            <span className="relative inline-block">
              <span className="relative z-10">On te trouve le meilleur prix.</span>
              <motion.span
                initial={{ width: 0 }}
                whileInView={{ width: "100%" }}
                viewport={{ once: true }}
                transition={{ duration: 0.8, delay: 0.3 }}
                className="absolute bottom-1 left-0 h-3 bg-yellow-400/30 -z-0 rounded-sm"
              />
            </span>
          </h2>
          <p className="mt-5 text-black/35 max-w-xl mx-auto text-base sm:text-lg">
            SwipeWear cherche la meme piece sur toutes les plateformes et te montre ou elle est la moins chere.
          </p>
        </motion.div>

        {/* Price ladder card */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ duration: 0.7 }}
          className="rounded-3xl border border-black/[0.06] bg-white p-6 sm:p-10 shadow-sm hover:shadow-xl hover:shadow-black/[0.03] transition-shadow duration-500"
        >
          {/* Item header */}
          <div className="flex items-center gap-4 mb-10 pb-6 border-b border-black/[0.04]">
            <motion.div
              whileHover={{ rotate: 5, scale: 1.05 }}
              className="w-14 h-14 rounded-2xl bg-gradient-to-br from-yellow-50 to-yellow-100 border border-yellow-200/50 flex items-center justify-center shadow-sm"
            >
              <svg viewBox="0 0 24 24" className="w-7 h-7 text-yellow-500" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M2 18l4-4 4 4 8-12 4 4" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </motion.div>
            <div>
              <p className="font-bold text-lg text-black">Nike Air Max 90</p>
              <p className="text-sm text-black/35">Taille 42 &middot; Coloris blanc/noir</p>
            </div>
            <div className="ml-auto hidden sm:block">
              <span className="text-[10px] font-bold bg-yellow-100 text-yellow-700 px-3 py-1 rounded-full uppercase tracking-wider">
                4 offres trouvees
              </span>
            </div>
          </div>

          {/* Price bars */}
          <div className="space-y-6">
            {prices.map((item, i) => (
              <motion.div
                key={item.platform}
                initial={{ opacity: 0, x: -30 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.12 }}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2.5">
                    <span className="text-sm font-semibold text-black">{item.platform}</span>
                    {item.best && (
                      <motion.span
                        initial={{ scale: 0 }}
                        whileInView={{ scale: 1 }}
                        viewport={{ once: true }}
                        transition={{ delay: 0.5, type: "spring" }}
                        className="text-[10px] font-bold bg-yellow-400 text-black px-2.5 py-0.5 rounded-full uppercase tracking-wider"
                      >
                        Meilleur prix
                      </motion.span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-black/20">{item.condition}</span>
                    <span className={`text-base font-bold tabular-nums ${item.best ? "text-yellow-600" : "text-black/40"}`}>
                      {item.price}
                    </span>
                  </div>
                </div>
                <div className="h-2.5 rounded-full bg-black/[0.03] overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    whileInView={{ width: item.width }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.8, delay: 0.3 + i * 0.12, ease: [0.16, 1, 0.3, 1] }}
                    className={`h-full rounded-full ${
                      item.best
                        ? "bg-gradient-to-r from-yellow-400 to-yellow-500 shadow-sm shadow-yellow-400/30"
                        : "bg-black/[0.06]"
                    }`}
                  />
                </div>
              </motion.div>
            ))}
          </div>

          {/* Footer */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.8 }}
            className="mt-10 pt-6 border-t border-black/[0.04] flex items-center justify-between"
          >
            <p className="text-sm text-black/30">
              Economie potentielle : <span className="text-yellow-600 font-bold text-base">30 &euro;</span>
            </p>
            <div className="flex items-center gap-2 text-xs text-black/15 font-mono tracking-wider">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              Mise a jour en temps reel
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
