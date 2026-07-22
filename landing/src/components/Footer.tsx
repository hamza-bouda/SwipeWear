export function Footer() {
  return (
    <footer className="border-t border-white/5 py-8 px-4">
      <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="text-lg font-bold bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
            SwipeWear
          </span>
          <span className="text-xs text-white/20">
            &copy; {new Date().getFullYear()}
          </span>
        </div>
        <div className="flex items-center gap-6 text-xs text-white/30">
          <a href="#comment-ca-marche" className="hover:text-white/60 transition-colors">
            Comment ca marche
          </a>
          <a href="#faq" className="hover:text-white/60 transition-colors">
            FAQ
          </a>
          <span>Fait avec passion a Paris</span>
        </div>
      </div>
    </footer>
  );
}
