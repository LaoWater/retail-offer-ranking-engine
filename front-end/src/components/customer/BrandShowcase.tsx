export default function BrandShowcase() {
  const brands = [
    { name: 'METRO Chef', tagline: 'Performanta si precizie', color: '#003B7E' },
    { name: 'aro', tagline: 'Cel mai bun raport calitate-pret', color: '#E63312' },
    { name: 'Rioba', tagline: 'Solutii profesionale de cafea', color: '#4E342E' },
    { name: 'METRO Professional', tagline: 'Echipamente pentru profesionisti', color: '#455A64' },
  ];

  return (
    <div>
      <h3 className="text-lg font-bold text-metro-gray-900 mb-4">Marci proprii METRO</h3>

      {/* Main METRO Chef banner */}
      <div className="bg-gradient-to-r from-metro-blue to-metro-blue-light rounded-2xl p-8 text-white mb-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-black mb-1">METRO Chef</div>
            <div className="text-white/80 text-sm">Performanta si precizie in bucatarie</div>
            <p className="text-white/60 text-xs mt-3 max-w-md">
              Gama noastra premium de produse alimentare, creata pentru profesionistii din gastronomie.
              Calitate de brand A la pretul marcii proprii.
            </p>
          </div>
          <div className="hidden md:block text-6xl font-black text-white/10">MC</div>
        </div>
      </div>

      {/* Other brands */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {brands.slice(1).map((b) => (
          <div
            key={b.name}
            className="bg-white rounded-xl p-4 border border-metro-gray-100 hover:shadow-md transition-shadow cursor-pointer"
          >
            <div className="text-sm font-bold mb-1" style={{ color: b.color }}>
              {b.name}
            </div>
            <div className="text-xs text-metro-gray-500">{b.tagline}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
