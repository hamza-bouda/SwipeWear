"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";

function ConfirmContent() {
  const params = useSearchParams();
  const status = params.get("status");

  const isOk = status === "ok";
  const isAlready = status === "already";

  return (
    <main className="min-h-screen flex items-center justify-center px-4 bg-white">
      <div className="max-w-md w-full text-center">
        <p className="text-4xl mb-6">{isOk ? "🎉" : isAlready ? "✅" : "❌"}</p>

        <h1 className="text-2xl font-black text-black mb-3">
          {isOk
            ? "Tu es sur la liste !"
            : isAlready
            ? "Déjà confirmé"
            : "Lien invalide"}
        </h1>

        <p className="text-black/40 text-sm leading-relaxed mb-8">
          {isOk
            ? "Email confirmé. Tu seras parmi les premiers prévenus au lancement de SwipeWear. Pas de spam — juste un email quand c'est prêt."
            : isAlready
            ? "Ton email était déjà confirmé. Tu es bien sur la liste !"
            : "Ce lien de confirmation est expiré ou déjà utilisé. Réinscris-toi si besoin."}
        </p>

        <Link
          href="/"
          className="inline-block bg-black text-white text-sm font-bold px-8 py-3.5 rounded-xl hover:bg-black/80 transition-colors"
        >
          Retour à l&apos;accueil
        </Link>

        <p className="mt-6 text-xs text-black/20">
          Swipe<span className="text-accent-dim font-bold">Wear</span>
        </p>
      </div>
    </main>
  );
}

export default function ConfirmePage() {
  return (
    <Suspense>
      <ConfirmContent />
    </Suspense>
  );
}
