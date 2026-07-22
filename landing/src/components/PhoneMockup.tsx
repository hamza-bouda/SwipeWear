"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence, type PanInfo } from "framer-motion";
import Image from "next/image";

const cards = [
  {
    brand: "NIKE",
    title: "Air Max 90 Vintage",
    price: "45 €",
    condition: "Like new",
    size: "42",
    image: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=500&fit=crop",
  },
  {
    brand: "THE NORTH FACE",
    title: "Nuptse 700 Puffer",
    price: "89 €",
    condition: "Tres bon",
    size: "M",
    image: "https://images.unsplash.com/photo-1544966503-7cc5ac882d5f?w=400&h=500&fit=crop",
  },
  {
    brand: "LEVI'S",
    title: "501 Original Fit",
    price: "32 €",
    condition: "Bon etat",
    size: "32",
    image: "https://images.unsplash.com/photo-1542272604-787c3835535d?w=400&h=500&fit=crop",
  },
  {
    brand: "ADIDAS",
    title: "Samba OG White",
    price: "55 €",
    condition: "Comme neuf",
    size: "43",
    image: "https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=400&h=500&fit=crop",
  },
  {
    brand: "CARHARTT",
    title: "Michigan Chore Coat",
    price: "67 €",
    condition: "Good",
    size: "L",
    image: "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=400&h=500&fit=crop",
  },
];

function SwipeCard({
  card,
  isTop,
  onSwipe,
}: {
  card: (typeof cards)[0];
  isTop: boolean;
  onSwipe: (dir: "left" | "right") => void;
}) {
  const handleDragEnd = (_: unknown, info: PanInfo) => {
    if (Math.abs(info.offset.x) > 60) {
      onSwipe(info.offset.x > 0 ? "right" : "left");
    }
  };

  return (
    <motion.div
      className="absolute inset-0"
      style={{ zIndex: isTop ? 2 : 1 }}
      initial={isTop ? { scale: 1 } : { scale: 0.95, y: 8 }}
      animate={isTop ? { scale: 1, y: 0 } : { scale: 0.95, y: 8 }}
      transition={{ duration: 0.3 }}
    >
      <motion.div
        className="w-full h-full rounded-2xl overflow-hidden bg-[#111] relative cursor-grab active:cursor-grabbing select-none"
        drag={isTop ? "x" : false}
        dragConstraints={{ left: 0, right: 0 }}
        dragElastic={0.9}
        onDragEnd={isTop ? handleDragEnd : undefined}
        whileDrag={{ rotate: 5 }}
        exit={{
          x: 250,
          opacity: 0,
          rotate: 15,
          transition: { duration: 0.4 },
        }}
      >
        {/* Product image */}
        <Image
          src={card.image}
          alt={card.title}
          fill
          className="object-cover"
          sizes="240px"
          draggable={false}
        />

        {/* Top badges */}
        <div className="absolute top-3 right-3 z-10">
          <span className="bg-yellow-400 text-black text-[8px] font-bold px-2 py-0.5 rounded-full uppercase">
            NEW
          </span>
        </div>

        {/* Bottom info overlay */}
        <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black via-black/80 to-transparent p-3 pt-10 z-10">
          <div className="flex items-center gap-1 mb-1">
            <span className="text-[8px] bg-white/15 backdrop-blur-sm rounded px-1.5 py-0.5 text-white/80">
              {card.condition}
            </span>
            <span className="text-[8px] bg-white/15 backdrop-blur-sm rounded px-1.5 py-0.5 text-white/80">
              {card.size}
            </span>
          </div>
          <p className="text-[9px] text-white/50">{card.brand}</p>
          <p className="text-[11px] font-semibold text-white">{card.title}</p>
          <div className="flex justify-between items-center mt-1">
            <span className="text-sm font-bold text-yellow-400">
              {card.price}
            </span>
            <div className="w-5 h-5 rounded-full bg-white/10 flex items-center justify-center">
              <span className="text-[8px] text-white">&hearts;</span>
            </div>
          </div>
        </div>

        {/* LIKE label on drag */}
        {isTop && (
          <motion.div
            className="absolute top-5 left-3 z-20 border-2 border-yellow-400 rounded-lg px-2 py-0.5 pointer-events-none"
            initial={{ opacity: 0 }}
            style={{ opacity: 0 }}
            whileDrag={{ opacity: 1 }}
          >
            <span className="text-xs font-extrabold text-yellow-400">
              LIKE
            </span>
          </motion.div>
        )}
      </motion.div>
    </motion.div>
  );
}

export function PhoneMockup() {
  const [index, setIndex] = useState(0);
  const [autoSwipe, setAutoSwipe] = useState(true);

  const handleSwipe = useCallback(() => {
    setIndex((prev) => (prev + 1) % cards.length);
  }, []);

  useEffect(() => {
    if (!autoSwipe) return;
    const timer = setInterval(() => {
      handleSwipe();
    }, 3000);
    return () => clearInterval(timer);
  }, [autoSwipe, handleSwipe]);

  const topCard = cards[index];
  const nextCard = cards[(index + 1) % cards.length];

  return (
    <motion.div
      initial={{ opacity: 0, y: 40, rotateY: -8 }}
      animate={{ opacity: 1, y: 0, rotateY: 0 }}
      transition={{ duration: 0.9, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className="relative mx-auto w-[280px] sm:w-[300px]"
    >
      {/* Glow behind phone */}
      <div className="absolute -inset-8 rounded-full bg-gradient-to-br from-yellow-400/10 to-amber-500/5 blur-3xl" />

      {/* Phone frame */}
      <div className="relative rounded-[2.5rem] border border-black/10 bg-gradient-to-b from-[#1a1a1a] to-[#0d0d0d] p-3 shadow-2xl shadow-black/20">
        {/* Notch */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-28 h-6 bg-black rounded-b-2xl z-30" />

        {/* Screen */}
        <div className="relative rounded-[2rem] overflow-hidden bg-black aspect-[9/19.5]">
          {/* Status bar */}
          <div className="flex items-center justify-between px-6 pt-3 pb-1 relative z-20">
            <span className="text-[10px] text-white/50 font-medium">9:41</span>
            <div className="flex gap-1">
              <div className="w-3.5 h-2 rounded-sm bg-white/50" />
              <div className="w-2 h-2 rounded-full bg-white/50" />
            </div>
          </div>

          {/* App header */}
          <div className="px-4 py-2 text-center relative z-20">
            <span className="text-sm font-bold text-white tracking-wide">
              Swipe<span className="text-yellow-400">Wear</span>
            </span>
          </div>

          {/* Swipeable cards area */}
          <div
            className="relative mx-3 aspect-[3/4] mb-2"
            onMouseDown={() => setAutoSwipe(false)}
            onTouchStart={() => setAutoSwipe(false)}
          >
            <AnimatePresence mode="popLayout">
              {/* Next card (behind) */}
              <SwipeCard
                key={`next-${(index + 1) % cards.length}`}
                card={nextCard}
                isTop={false}
                onSwipe={() => {}}
              />
              {/* Top card */}
              <SwipeCard
                key={`top-${index}`}
                card={topCard}
                isTop={true}
                onSwipe={handleSwipe}
              />
            </AnimatePresence>
          </div>

          {/* Bottom nav dots */}
          <div className="flex justify-center gap-8 pt-2 pb-2 relative z-20">
            <div className="w-8 h-8 rounded-full border border-white/10 flex items-center justify-center">
              <span className="text-white/30 text-xs">&times;</span>
            </div>
            <div className="w-8 h-8 rounded-full border border-yellow-400/40 flex items-center justify-center">
              <span className="text-yellow-400 text-xs">&hearts;</span>
            </div>
          </div>
        </div>
      </div>

      {/* Floating particles */}
      <motion.div
        animate={{ y: [-10, 10, -10], x: [-5, 5, -5] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
        className="absolute -top-4 -right-4 w-2 h-2 rounded-full bg-yellow-400/40 blur-[2px]"
      />
      <motion.div
        animate={{ y: [10, -10, 10], x: [5, -5, 5] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
        className="absolute -bottom-2 -left-6 w-3 h-3 rounded-full bg-yellow-300/20 blur-[2px]"
      />
    </motion.div>
  );
}
