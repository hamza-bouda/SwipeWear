"use client";

import { motion } from "framer-motion";

export function PhoneMockup() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 40, rotateY: -8 }}
      animate={{ opacity: 1, y: 0, rotateY: 0 }}
      transition={{ duration: 0.9, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className="relative mx-auto w-[280px] sm:w-[300px]"
    >
      {/* Glow behind phone */}
      <div className="absolute -inset-8 rounded-full bg-gradient-to-br from-violet-600/20 to-purple-500/10 blur-3xl" />

      {/* Phone frame */}
      <div className="relative rounded-[2.5rem] border-2 border-white/10 bg-gradient-to-b from-[#1a1a1a] to-[#0d0d0d] p-3 shadow-2xl shadow-purple-900/20">
        {/* Notch */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-28 h-6 bg-black rounded-b-2xl z-10" />

        {/* Screen */}
        <div className="relative rounded-[2rem] overflow-hidden bg-[#0a0a0a] aspect-[9/19.5]">
          {/* Status bar */}
          <div className="flex items-center justify-between px-6 pt-3 pb-1">
            <span className="text-[10px] text-white/60 font-medium">9:41</span>
            <div className="flex gap-1">
              <div className="w-3.5 h-2 rounded-sm bg-white/60" />
              <div className="w-2 h-2 rounded-full bg-white/60" />
            </div>
          </div>

          {/* App header */}
          <div className="px-4 py-2 text-center">
            <span className="text-sm font-bold text-white tracking-wide">SwipeWear</span>
          </div>

          {/* Card */}
          <div className="px-3 pt-1">
            <motion.div
              animate={{ rotate: [0, -2, 0, 2, 0] }}
              transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
              className="relative rounded-2xl overflow-hidden bg-gradient-to-br from-violet-900/60 to-purple-800/40 aspect-[3/4] shadow-xl"
            >
              {/* Fake product image pattern */}
              <div className="absolute inset-0 opacity-30">
                <div className="absolute top-4 left-4 w-8 h-8 rounded-full bg-white/20" />
                <div className="absolute top-4 right-4 rounded-full bg-emerald-400/30 px-2 py-0.5 text-[8px] text-white">NEW</div>
              </div>

              {/* Sneaker silhouette */}
              <div className="absolute inset-0 flex items-center justify-center">
                <svg viewBox="0 0 120 60" className="w-32 opacity-40" fill="none">
                  <path d="M10 45 Q15 20 40 18 Q55 16 65 22 L95 28 Q110 30 115 38 L115 45 Q110 50 90 48 L20 48 Q12 48 10 45Z" fill="white" />
                  <path d="M40 18 Q50 10 65 22" stroke="white" strokeWidth="2" opacity="0.5" />
                  <circle cx="25" cy="44" r="8" fill="none" stroke="white" strokeWidth="1.5" opacity="0.3" />
                  <circle cx="100" cy="42" r="8" fill="none" stroke="white" strokeWidth="1.5" opacity="0.3" />
                </svg>
              </div>

              {/* Bottom info */}
              <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 to-transparent p-3">
                <div className="flex items-center gap-1 mb-1">
                  <span className="text-[8px] bg-white/20 rounded px-1.5 py-0.5 text-white">Like new</span>
                  <span className="text-[8px] bg-white/20 rounded px-1.5 py-0.5 text-white">42</span>
                </div>
                <p className="text-[10px] text-white/60">NIKE</p>
                <p className="text-xs font-semibold text-white">Air Max 90 Vintage</p>
                <div className="flex justify-between items-center mt-1">
                  <span className="text-sm font-bold text-white">45 &euro;</span>
                  <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center">
                    <span className="text-[10px]">&hearts;</span>
                  </div>
                </div>
              </div>

              {/* LIKE overlay */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: [0, 0, 0, 0.8, 0] }}
                transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", times: [0, 0.5, 0.6, 0.7, 0.85] }}
                className="absolute top-6 left-3 border-2 border-emerald-400 rounded-lg px-2 py-1"
              >
                <span className="text-sm font-extrabold text-emerald-400">LIKE</span>
              </motion.div>
            </motion.div>
          </div>

          {/* Bottom nav dots */}
          <div className="flex justify-center gap-8 pt-4 pb-2">
            <div className="w-8 h-8 rounded-full border border-red-400/40 flex items-center justify-center">
              <span className="text-red-400 text-xs">&times;</span>
            </div>
            <div className="w-8 h-8 rounded-full border border-emerald-400/40 flex items-center justify-center">
              <span className="text-emerald-400 text-xs">&hearts;</span>
            </div>
          </div>
        </div>
      </div>

      {/* Floating particles */}
      <motion.div
        animate={{ y: [-10, 10, -10], x: [-5, 5, -5] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
        className="absolute -top-4 -right-4 w-3 h-3 rounded-full bg-violet-500/40 blur-sm"
      />
      <motion.div
        animate={{ y: [10, -10, 10], x: [5, -5, 5] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
        className="absolute -bottom-2 -left-6 w-4 h-4 rounded-full bg-purple-400/30 blur-sm"
      />
    </motion.div>
  );
}
