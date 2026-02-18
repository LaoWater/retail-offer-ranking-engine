import { useState, useMemo } from 'react';
import { useRecommendations } from '../api/hooks';
import type { OfferRecommendation } from '../types/metro';
import CustomerSelector from '../components/customer/CustomerSelector';
import WelcomeBar from '../components/customer/WelcomeBar';
import CategoryTabs from '../components/customer/CategoryTabs';
import ProductGrid from '../components/customer/ProductGrid';
import ProductDetail from '../components/customer/ProductDetail';
import AlgorithmToggle from '../components/customer/AlgorithmToggle';
import CategoryBrowse from '../components/customer/CategoryBrowse';
import BrandShowcase from '../components/customer/BrandShowcase';

export default function CustomerPage() {
  const [customerId, setCustomerId] = useState<number | null>(null);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [selectedRec, setSelectedRec] = useState<OfferRecommendation | null>(null);

  const { data: recData, isLoading } = useRecommendations(customerId);
  const recs = recData?.recommendations ?? [];

  // Derive unique categories from recommendations
  const categories = useMemo(() => {
    const cats = [...new Set(recs.map((r) => r.category))];
    return cats;
  }, [recs]);

  // Filter by active category
  const filteredRecs = activeCategory
    ? recs.filter((r) => r.category === activeCategory)
    : recs;

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Customer selector */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <CustomerSelector selectedId={customerId} onSelect={setCustomerId} />
        {recData && (
          <span className="text-xs text-metro-gray-500 font-mono">
            Data: {recData.run_date}
          </span>
        )}
      </div>

      {/* Welcome bar */}
      {customerId && <WelcomeBar customerId={customerId} />}

      {/* Recommendations section */}
      {customerId && (
        <div className="space-y-4">
          <h3 className="text-lg font-bold text-metro-gray-900 font-heading">
            Oferte personalizate pentru tine
          </h3>

          {/* Category filter tabs */}
          {categories.length > 0 && (
            <CategoryTabs
              categories={categories}
              activeCategory={activeCategory}
              onSelect={setActiveCategory}
            />
          )}

          {/* Loading */}
          {isLoading && (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {Array.from({ length: 10 }).map((_, i) => (
                <div key={i} className="bg-white rounded-xl overflow-hidden shadow-sm">
                  <div className="skeleton aspect-square" />
                  <div className="p-3 space-y-2">
                    <div className="skeleton h-3 w-16" />
                    <div className="skeleton h-4 w-full" />
                    <div className="skeleton h-3 w-24" />
                    <div className="skeleton h-5 w-20" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Product grid */}
          {!isLoading && (
            <ProductGrid
              recommendations={filteredRecs}
              onCardClick={setSelectedRec}
            />
          )}

          {/* Algorithm toggle */}
          <AlgorithmToggle />
        </div>
      )}

      {/* Empty state */}
      {!customerId && (
        <div className="text-center py-20">
          <div className="inline-flex items-center justify-center w-24 h-24 rounded-2xl bg-metro-blue/5 mb-6">
            {/* Stylized person + data dots SVG */}
            <svg className="w-12 h-12 text-metro-blue" fill="none" stroke="currentColor" viewBox="0 0 48 48" strokeWidth={1.5}>
              <circle cx="24" cy="14" r="7" />
              <path strokeLinecap="round" d="M10 40c0-7.732 6.268-14 14-14s14 6.268 14 14" />
              <circle cx="38" cy="10" r="2" fill="currentColor" opacity="0.3" />
              <circle cx="42" cy="16" r="1.5" fill="currentColor" opacity="0.2" />
              <circle cx="36" cy="5" r="1" fill="currentColor" opacity="0.15" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-metro-gray-900 mb-2 font-heading">
            Selecteaza un client METRO
          </h2>
          <p className="text-metro-gray-500 max-w-md mx-auto">
            Alege un client din baza de date pentru a vedea ofertele personalizate
            generate de modelul ML.
          </p>
        </div>
      )}

      {/* Category browse & brand showcase */}
      <div className="space-y-8 pt-8 border-t border-metro-gray-200">
        <CategoryBrowse />
        <BrandShowcase />
      </div>

      {/* Product detail modal */}
      <ProductDetail rec={selectedRec} onClose={() => setSelectedRec(null)} />
    </div>
  );
}
