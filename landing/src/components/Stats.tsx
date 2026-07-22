"use client";

import { motion, useInView } from "framer-motion";
import { useRef, useEffect, useState } from "react";

function AnimatedCounter({ target, suffix = "" }: { target: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!isInView) return;
    let start = 0;
    const step = Math.ceil(target / 40);
    const timer = setInterval(() => {
      start += step;
      if (start >= target) {
        setCount(target);
        clearInterval(timer);
      } else {
        setCount(start);
      }
    }, 30);
    return () => clearInterval(timer);
  }, [isInView, target]);

  return <span ref={ref}>{count.toLocaleString("fr-FR")}{suffix}</span>;
}

const stats = [
  { value: 50000, suffix: "+", label: "Pieces scannees", icon: "&#128083;" },
  { value: 30, suffix: "%", label: "Economie moyenne", icon: "&#128176;" },
  { value: 4, suffix: "+", label: "Sources comparees", icon: "&#128269;" },
  { value: 500, suffix: "ms", label: "Temps de reponse IA", icon: "&#9889;" },
];

export function Stats() {
  return (
    <section className="relative py-20 px-4">
      <div className="max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="grid grid-cols-2 lg:grid-cols-4 gap-6"
        >
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className="text-center p-6 rounded-2xl bg-neutral-50/50 border border-black/[0.03] hover:border-yellow-400/20 transition-colors"
            >
              <div className="text-2xl mb-3" dangerouslySetInnerHTML={{ __html: stat.icon }} />
              <div className="text-3xl sm:text-4xl font-black text-black mb-1 tabular-nums">
                <AnimatedCounter target={stat.value} suffix={stat.suffix} />
              </div>
              <p className="text-xs sm:text-sm text-black/30 font-medium">{stat.label}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
