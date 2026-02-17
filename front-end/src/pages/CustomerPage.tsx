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
          <span className="text-xs text-metro-gray-500">
            Data: {recData.run_date}
          </span>
        )}
      </div>

      {/* Welcome bar */}
      {customerId && <WelcomeBar customerId={customerId} />}

      {/* Recommendations section */}
      {customerId && (
        <div className="space-y-4">
          <h3 className="text-lg font-bold text-metro-gray-900">
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
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-metro-blue/10 mb-6">
            <svg className="w-10 h-10 text-metro-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-metro-gray-900 mb-2">
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
