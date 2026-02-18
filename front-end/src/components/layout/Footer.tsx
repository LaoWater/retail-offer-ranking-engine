export default function Footer() {
  return (
    <footer className="bg-metro-gray-900 text-white/60 mt-auto">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="bg-metro-yellow text-metro-blue font-heading font-black text-sm px-1.5 py-0.5 rounded">
              METRO
            </div>
            <span className="text-sm font-heading font-medium">Cash & Carry Romania</span>
          </div>

          <div className="text-xs text-center md:text-right space-y-1">
            <p className="font-heading font-medium">ML-Powered Personalized Offers Recommender</p>
            <p className="text-white/40 flex items-center gap-2 justify-center md:justify-end">
              <span className="inline-flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-metro-green" />
                Phase 1: Classical ML (LightGBM)
              </span>
              <span className="text-white/20">|</span>
              <span className="text-white/30">Phase 2: Deep Learning (Planned)</span>
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
