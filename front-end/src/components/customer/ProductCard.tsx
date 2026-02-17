import { motion } from 'framer-motion';
import type { OfferRecommendation } from '../../types/metro';
import { CATEGORY_DISPLAY, OFFER_TYPE_DISPLAY } from '../../types/metro';

interface Props {
  rec: OfferRecommendation;
  index: number;
  onClick: () => void;
}

export default function ProductCard({ rec, index, onClick }: Props) {
  const hasDiscount = rec.discount_value > 0;
  const discountPct = rec.offer_type === 'percentage'
    ? Math.round(rec.discount_value)
    : Math.round((rec.discount_value / rec.tier1_price) * 100);

  const discountedPrice = rec.offer_type === 'percentage'
    ? rec.tier1_price * (1 - rec.discount_value / 100)
    : rec.tier1_price - rec.discount_value;

  const netPrice = discountedPrice / 1.19; // VAT 19% Romania

  // Generate a deterministic product image placeholder color based on category
  const categoryColors: Record<string, string> = {
    meat_poultry: '#D32F2F',
    seafood: '#0288D1',
    dairy_eggs: '#FFF9C4',
    fruits_vegetables: '#4CAF50',
    beverages_non_alcoholic: '#29B6F6',
    bakery_pastry: '#D7A86E',
    frozen_foods: '#90CAF9',
    grocery_staples: '#8D6E63',
    beverages_alcoholic: '#7B1FA2',
    confectionery_snacks: '#E91E63',
    deli_charcuterie: '#BF360C',
    condiments_spices: '#FF8F00',
    coffee_tea: '#4E342E',
    cleaning_detergents: '#00BCD4',
    kitchen_utensils_tableware: '#607D8B',
    horeca_equipment: '#455A64',
    paper_packaging: '#A1887F',
    personal_care_hygiene: '#E8EAF6',
    household_goods: '#78909C',
    office_supplies: '#9E9E9E',
    electronics_small_appliances: '#37474F',
  };

  const bgColor = categoryColors[rec.category] || '#9E9E9E';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className="product-card bg-white rounded-xl overflow-hidden cursor-pointer shadow-sm border border-metro-gray-100"
      onClick={onClick}
    >
      {/* Discount badge */}
      {hasDiscount && discountPct > 0 && (
        <div className="absolute top-3 left-3 z-10">
          <span className="bg-metro-red text-white text-xs font-bold px-2 py-1 rounded">
            -{discountPct}%
          </span>
        </div>
      )}

      {/* Product image placeholder */}
      <div className="relative aspect-square bg-metro-gray-50 flex items-center justify-center p-4">
        <div
          className="w-24 h-24 rounded-xl flex items-center justify-center text-white text-3xl font-bold opacity-80"
          style={{ backgroundColor: bgColor }}
        >
          {(CATEGORY_DISPLAY[rec.category] || rec.category).charAt(0)}
        </div>

        {/* Rank badge */}
        <div className="absolute top-2 right-2 bg-metro-blue/90 text-white text-[10px] font-bold w-6 h-6 rounded-full flex items-center justify-center">
          #{rec.rank}
        </div>
      </div>

      {/* Product info */}
      <div className="p-3">
        {/* Brand */}
        <div className="text-[10px] font-semibold text-metro-blue uppercase tracking-wide mb-1">
          {rec.brand}
        </div>

        {/* Product name */}
        <div className="text-sm font-medium text-metro-gray-900 line-clamp-2 min-h-[2.5rem] mb-1">
          {rec.brand} {CATEGORY_DISPLAY[rec.category] || rec.category}
        </div>

        {/* Category */}
        <div className="text-xs text-metro-gray-500 mb-2">
          {CATEGORY_DISPLAY[rec.category] || rec.category}
        </div>

        {/* Availability */}
        <div className="flex items-center gap-1 mb-2">
          <div className="w-2 h-2 rounded-full bg-metro-green" />
          <span className="text-[10px] text-metro-gray-500">disponibil in METRO Cluj</span>
        </div>

        {/* Tier pricing hint */}
        <div className="text-[11px] text-metro-blue font-medium mb-2">
          Cumperi mai mult, platesti mai putin
        </div>

        {/* Pricing */}
        <div className="space-y-0.5">
          {hasDiscount ? (
            <>
              <div className="text-sm text-metro-gray-400 line-through">
                {rec.tier1_price.toFixed(2)} lei
              </div>
              <div className="text-lg font-bold text-metro-gray-900">
                {discountedPrice.toFixed(2)} lei
              </div>
              <div className="text-xs text-metro-gray-500">
                {netPrice.toFixed(2)} lei excl. TVA
              </div>
            </>
          ) : (
            <>
              <div className="text-lg font-bold text-metro-gray-900">
                {rec.tier1_price.toFixed(2)} lei
              </div>
              <div className="text-xs text-metro-gray-500">
                {(rec.tier1_price / 1.19).toFixed(2)} lei excl. TVA
              </div>
            </>
          )}
        </div>

        {/* Offer type badge */}
        <div className="mt-2">
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-metro-orange/10 text-metro-orange font-medium">
            {OFFER_TYPE_DISPLAY[rec.offer_type] || rec.offer_type}
          </span>
        </div>
      </div>
    </motion.div>
  );
}
