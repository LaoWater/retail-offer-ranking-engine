import type { OfferRecommendation } from '../../types/metro';
import ProductCard from './ProductCard';

interface Props {
  recommendations: OfferRecommendation[];
  onCardClick: (rec: OfferRecommendation) => void;
}

export default function ProductGrid({ recommendations, onCardClick }: Props) {
  if (recommendations.length === 0) {
    return (
      <div className="text-center py-12 text-metro-gray-500">
        <svg className="w-16 h-16 mx-auto mb-4 text-metro-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
        </svg>
        <p className="text-lg font-medium">Nu exista recomandari</p>
        <p className="text-sm mt-1">Selecteaza un client pentru a vedea ofertele personalizate</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      {recommendations.map((rec, i) => (
        <ProductCard
          key={rec.offer_id}
          rec={rec}
          index={i}
          onClick={() => onCardClick(rec)}
        />
      ))}
    </div>
  );
}
