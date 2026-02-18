export default function BrandShowcase() {
  return (
    <div>
      <h3 className="text-lg font-bold text-metro-gray-900 mb-4">Marci proprii METRO</h3>

      {/* Main METRO Chef banner */}
      <div className="relative bg-gradient-to-br from-metro-blue via-metro-blue to-metro-blue-light rounded-2xl p-8 text-white mb-4 overflow-hidden group hover:shadow-lg transition-shadow cursor-pointer">
        {/* Subtle pattern overlay */}
        <div className="absolute inset-0 opacity-[0.04]" style={{
          backgroundImage: `repeating-linear-gradient(45deg, transparent, transparent 20px, currentColor 20px, currentColor 21px)`,
        }} />
        <div className="relative flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="font-heading text-3xl font-black tracking-tight">METRO</span>
              <span className="font-heading text-3xl font-light italic text-white/90">Chef</span>
            </div>
            <div className="text-white/80 text-sm font-medium">Performanta si precizie in bucatarie</div>
            <p className="text-white/50 text-xs mt-3 max-w-md leading-relaxed">
              Gama noastra premium de produse alimentare, creata pentru profesionistii din gastronomie.
              Calitate de brand A la pretul marcii proprii.
            </p>
          </div>
          <div className="hidden md:flex items-center justify-center w-20 h-20 rounded-2xl bg-white/10 group-hover:bg-white/15 transition-colors">
            <span className="font-heading text-4xl font-black text-white/30">MC</span>
          </div>
        </div>
      </div>

      {/* Other brands */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* aro */}
        <div className="bg-white rounded-xl p-5 border border-metro-gray-100 hover-lift cursor-pointer group">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-heading text-xl font-black lowercase text-metro-red tracking-tight">aro</span>
            <div className="h-px flex-1 bg-metro-red/15" />
          </div>
          <div className="text-xs text-metro-gray-500 leading-relaxed">Cel mai bun raport calitate-pret</div>
        </div>

        {/* Rioba */}
        <div className="bg-white rounded-xl p-5 border border-metro-gray-100 hover-lift cursor-pointer group">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-heading text-xl font-medium italic" style={{ color: '#4E342E' }}>Rioba</span>
            <div className="h-px flex-1" style={{ backgroundColor: 'rgba(78,52,46,0.15)' }} />
          </div>
          <div className="text-xs text-metro-gray-500 leading-relaxed">Solutii profesionale de cafea</div>
        </div>

        {/* METRO Professional */}
        <div className="bg-white rounded-xl p-5 border border-metro-gray-100 hover-lift cursor-pointer group">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-heading text-sm font-bold uppercase tracking-[0.2em]" style={{ color: '#455A64' }}>METRO Professional</span>
          </div>
          <div className="h-px w-12 mb-2" style={{ backgroundColor: 'rgba(69,90,100,0.3)' }} />
          <div className="text-xs text-metro-gray-500 leading-relaxed">Echipamente pentru profesionisti</div>
        </div>
      </div>
    </div>
  );
}
