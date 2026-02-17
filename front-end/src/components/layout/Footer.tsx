export default function Footer() {
  return (
    <footer className="bg-metro-gray-900 text-white/60 mt-auto">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="bg-metro-yellow text-metro-blue font-black text-sm px-1.5 py-0.5 rounded">
              METRO
            </div>
            <span className="text-sm">Cash & Carry Romania</span>
          </div>

          <div className="text-xs text-center md:text-right space-y-1">
            <p>ML-Powered Personalized Offers Recommender</p>
            <p className="text-white/40">
              Phase 1: Classical ML (LightGBM) | Phase 2: Deep Learning (Planned)
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
