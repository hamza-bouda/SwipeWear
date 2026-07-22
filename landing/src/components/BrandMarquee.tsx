"use client";

import { motion } from "framer-motion";

const brands = [
  "NIKE", "ADIDAS", "THE NORTH FACE", "LEVI'S", "CARHARTT",
  "NEW BALANCE", "STUSSY", "RALPH LAUREN", "PATAGONIA", "DICKIES",
  "CHAMPION", "CONVERSE", "VANS", "SUPREME", "STONE ISLAND",
];

export function BrandMarquee() {
  return (
    <motion.section
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.8 }}
      className="relative py-10 overflow-hidden border-y border-black/[0.04]"
    >
      <div className="absolute inset-0 bg-gradient-to-r from-white via-transparent to-white z-10 pointer-events-none" />
      <div className="flex animate-marquee whitespace-nowrap">
        {[...brands, ...brands].map((brand, i) => (
          <span
            key={`${brand}-${i}`}
            className="mx-8 sm:mx-12 text-sm sm:text-base font-bold tracking-[0.2em] text-black/[0.08] uppercase select-none shrink-0"
          >
            {brand}
          </span>
        ))}
      </div>
    </motion.section>
  );
}
