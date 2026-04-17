"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence, type PanInfo } from "framer-motion";
import Image from "next/image";

const cards = [
  {
    brand: "NIKE",
    title: "Air Max 90",
    price: "45 €",
    condition: "Comme neuf",
    size: "42",
    image: "https://images.unsplash.com/photo-1515955656352-a1fa3ffcd111?w=400&h=500&fit=crop&q=80",
  },
  {
    brand: "THE NORTH FACE",
    title: "Puffer Jacket",
    price: "89 €",
    condition: "Tres bon",
    size: "M",
    image: "https://images.unsplash.com/photo-1614031679232-0dae776a72ee?w=400&h=500&fit=crop&q=80",
  },
  {
    brand: "LEVI'S",
    title: "Denim Jacket",
    price: "52 €",
    condition: "Bon etat",
    size: "M",
    image: "https://images.unsplash.com/photo-1611312449408-fcece27cdbb7?w=400&h=500&fit=crop&q=80",
  },
  {
    brand: "ADIDAS",
    title: "Originals Sneakers",
    price: "55 €",
    condition: "Comme neuf",
    size: "43",
    image: "https://images.unsplash.com/photo-1518002171953-a080ee817e1f?w=400&h=500&fit=crop&q=80",
  },
  {
    brand: "CARHARTT",
    title: "Michigan Chore Coat",
    price: "67 €",
    condition: "Good",
    size: "L",
    image: "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=400&h=500&fit=crop&q=80",
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
        className="w-full h-full rounded-2xl overflow-hidden bg-white relative cursor-grab active:cursor-grabbing select-none shadow-lg"
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
        <div className="relative w-full h-[70%]">
          <Image
            src={card.image}
            alt={`${card.brand} ${card.title} — ${card.price}`}
            fill
            className="object-cover"
            sizes="240px"
            draggable={false}
          />
          <div className="absolute top-2.5 right-2.5 z-10">
            <span className="bg-yellow-400 text-black text-[7px] font-bold px-1.5 py-0.5 rounded-full uppercase tracking-wide">
              NEW
            </span>
          </div>
        </div>

        <div className="px-3 py-2.5 bg-white">
          <div className="flex items-center gap-1 mb-1">
            <span className="text-[7px] bg-neutral-100 rounded-full px-1.5 py-0.5 text-neutral-500 font-medium">
              {card.condition}
            </span>
            <span className="text-[7px] bg-neutral-100 rounded-full px-1.5 py-0.5 text-neutral-500 font-medium">
              {card.size}
            </span>
          </div>
          <p className="text-[8px] text-neutral-400 uppercase tracking-wider font-medium">{card.brand}</p>
          <p className="text-[11px] font-semibold text-black leading-tight">{card.title}</p>
          <div className="flex justify-between items-center mt-1">
            <span className="text-sm font-bold text-yellow-500">
              {card.price}
            </span>
            <div className="w-5 h-5 rounded-full bg-neutral-100 flex items-center justify-center">
              <span className="text-[9px] text-neutral-400">&hearts;</span>
            </div>
          </div>
        </div>

        {isTop && (
          <motion.div
            className="absolute top-4 left-3 z-20 border-2 border-yellow-400 rounded-lg px-2 py-0.5 bg-yellow-400/10 pointer-events-none"
            initial={{ opacity: 0 }}
            style={{ opacity: 0 }}
            whileDrag={{ opacity: 1 }}
          >
            <span className="text-xs font-extrabold text-yellow-500">
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
      <div className="absolute -inset-8 rounded-full bg-gradient-to-br from-yellow-400/10 to-amber-500/5 blur-3xl animate-pulse-glow" />

      {/* Phone frame */}
      <div className="relative rounded-[2.5rem] border border-neutral-200 bg-gradient-to-b from-neutral-800 to-neutral-900 p-3 shadow-2xl shadow-black/15">
        {/* Notch */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-28 h-6 bg-black rounded-b-2xl z-30" />

        {/* Screen */}
        <div className="relative rounded-[2rem] overflow-hidden bg-white aspect-[9/19.5]">
          {/* Status bar */}
          <div className="flex items-center justify-between px-6 pt-3 pb-1 relative z-20">
            <span className="text-[10px] text-black/40 font-medium">9:41</span>
            <div className="flex gap-1">
              <div className="w-3.5 h-2 rounded-sm bg-black/30" />
              <div className="w-2 h-2 rounded-full bg-black/30" />
            </div>
          </div>

          {/* App header */}
          <div className="px-4 py-1.5 text-center relative z-20">
            <span className="text-sm font-bold text-black tracking-wide">
              Swipe<span className="text-yellow-500">Wear</span>
            </span>
          </div>

          {/* Swipeable cards area */}
          <div
            className="relative mx-3 aspect-[3/4] mb-2"
            onMouseDown={() => setAutoSwipe(false)}
            onTouchStart={() => setAutoSwipe(false)}
          >
            <AnimatePresence mode="popLayout">
              <SwipeCard
                key={`next-${(index + 1) % cards.length}`}
                card={nextCard}
                isTop={false}
                onSwipe={() => {}}
              />
              <SwipeCard
                key={`top-${index}`}
                card={topCard}
                isTop={true}
                onSwipe={handleSwipe}
              />
            </AnimatePresence>
          </div>

          {/* Bottom action buttons */}
          <div className="flex justify-center gap-8 pt-1 pb-2 relative z-20">
            <div className="w-8 h-8 rounded-full border border-neutral-200 flex items-center justify-center bg-white shadow-sm">
              <span className="text-neutral-400 text-xs">&times;</span>
            </div>
            <div className="w-8 h-8 rounded-full border border-yellow-300 flex items-center justify-center bg-yellow-50 shadow-sm">
              <span className="text-yellow-500 text-xs">&hearts;</span>
            </div>
          </div>

          {/* Bottom tab bar */}
          <div className="absolute bottom-0 inset-x-0 flex justify-around items-center py-2 px-4 border-t border-neutral-100 bg-white/90 backdrop-blur-sm z-20">
            <div className="flex flex-col items-center">
              <span className="text-[9px]">&#128293;</span>
              <span className="text-[6px] font-medium text-black mt-0.5">Feed</span>
            </div>
            <div className="flex flex-col items-center opacity-40">
              <span className="text-[9px]">&#10084;&#65039;</span>
              <span className="text-[6px] font-medium text-black/50 mt-0.5">Saves</span>
            </div>
            <div className="flex flex-col items-center opacity-40">
              <span className="text-[9px]">&#128100;</span>
              <span className="text-[6px] font-medium text-black/50 mt-0.5">Profile</span>
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
