export function Footer() {
  return (
    <footer className="border-t border-black/[0.05] py-8 px-4 bg-neutral-50">
      <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="text-lg font-black">
            Swipe<span className="text-accent-dim">Wear</span>
          </span>
          <span className="text-xs text-black/20">
            &copy; {new Date().getFullYear()}
          </span>
        </div>
        <div className="flex items-center gap-6 text-xs text-black/30">
          <a href="#comment-ca-marche" className="hover:text-black/60 transition-colors">
            Comment ca marche
          </a>
          <a href="#faq" className="hover:text-black/60 transition-colors">
            FAQ
          </a>
          <span>Fait avec passion a Paris</span>
        </div>
      </div>
    </footer>
  );
}
