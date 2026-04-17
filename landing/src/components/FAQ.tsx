"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const faqs = [
  {
    q: "C'est quoi SwipeWear exactement ?",
    a: "SwipeWear est une app mobile qui utilise l'intelligence artificielle pour te proposer des pieces de mode de seconde main adaptees a ton style. Tu swipes comme sur Tinder : like a droite, passe a gauche. Plus tu swipes, plus l'IA comprend ce que tu aimes.",
  },
  {
    q: "C'est gratuit ?",
    a: "Oui, l'app de base sera entierement gratuite. On se remunere via l'affiliation quand tu achetes une piece depuis l'app. Un abonnement Premium optionnel a 4,99 €/mois donnera acces a des alertes instantanees sur les bonnes affaires.",
  },
  {
    q: "Quelles plateformes sont couvertes ?",
    a: "Au lancement, SwipeWear agregera les annonces d'eBay (occasion) et de marketplaces partenaires (neuf via affiliation). D'autres sources seront ajoutees progressivement apres le lancement.",
  },
  {
    q: "Comment fonctionne l'echelle de prix ?",
    a: "Quand tu likes une piece, notre IA la cherche sur toutes les plateformes connectees et te montre une echelle de prix du moins cher au plus cher, avec l'etat de chaque annonce. Tu choisis, on te redirige.",
  },
  {
    q: "Quand est-ce que ca sort ?",
    a: "On est en phase de developpement. Inscris-toi a la waitlist pour etre prevenu(e) en premier au lancement et avoir acces a la beta en priorite.",
  },
];

function FAQItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="border-b border-black/[0.05]"
    >
      <button
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="flex items-center justify-between w-full py-5 text-left group cursor-pointer"
      >
        <span className="text-sm sm:text-base font-medium pr-4 text-black group-hover:text-accent-deep transition-colors">
          {q}
        </span>
        <motion.span
          animate={{ rotate: open ? 45 : 0 }}
          transition={{ duration: 0.2 }}
          className="text-black/20 text-xl shrink-0 group-hover:text-accent-dim transition-colors"
        >
          +
        </motion.span>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <p className="pb-5 text-sm text-black/40 leading-relaxed">
              {a}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function FAQ() {
  return (
    <section id="faq" className="relative py-24 sm:py-32 px-4 bg-neutral-50">
      <div className="relative max-w-2xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <span className="inline-block text-[11px] font-mono tracking-[0.2em] text-black/25 uppercase mb-4">
            FAQ
          </span>
          <h2 className="text-3xl sm:text-4xl font-bold text-black">
            Des questions ?
          </h2>
        </motion.div>

        <div>
          {faqs.map((faq) => (
            <FAQItem key={faq.q} {...faq} />
          ))}
        </div>
      </div>
    </section>
  );
}
