import { useState } from 'react';
import { motion } from 'framer-motion';
import type { OfferRecommendation } from '../../types/metro';
import { CATEGORY_DISPLAY, OFFER_TYPE_DISPLAY } from '../../types/metro';

interface Props {
  rec: OfferRecommendation;
  index: number;
  onClick: () => void;
}

// Curated Unsplash photo IDs per category — deterministic, no API key needed
const CATEGORY_PHOTOS: Record<string, string[]> = {
  meat_poultry: [
    '1607623814825-11cdae563a3d', // raw steak
    '1602473812024-4708fa8c1be1', // butcher meat
    '1588347818481-07a913c1d8b7', // chicken
  ],
  seafood: [
    '1534604973900-c43ab4c2e0ab', // fish market
    '1559709319-3e3fcaa3ed1b', // fresh fish
    '1615141982883-c7ad0e69fd62', // salmon fillet
  ],
  dairy_eggs: [
    '1628088062854-d1870b4553da', // cheese assortment
    '1559598467-f8b76c8155d0', // milk and dairy
    '1582722872445-44dc5f7e3c8f', // eggs
  ],
  fruits_vegetables: [
    '1610832958506-c8b927c2b8ff', // fresh vegetables
    '1597714026720-8f55c1a5e6d3', // fruits
    '1540420773420-3366772f4999', // colorful veggies
  ],
  beverages_non_alcoholic: [
    '1544145945-f90425340c7e', // water bottles
    '1556679343-c7306c1976bc', // juice
    '1625772299848-391b6a87d7b3', // soft drinks
  ],
  bakery_pastry: [
    '1509440159596-0249088772ff', // fresh bread
    '1517433670267-08bbd4be890f', // pastries
    '1555507036-ab1f4038024a', // baked goods
  ],
  frozen_foods: [
    '1584568694244-14fbdf83bd30', // frozen vegetables
    '1563805042-7684c019e1cb', // frozen food aisle
    '1488477181946-6428a0291777', // ice cream
  ],
  grocery_staples: [
    '1586201375761-83865001e31c', // pasta and grains
    '1556909114-f6e7ad7d3136', // rice and staples
    '1620706857370-e1b9770e8bb1', // cooking oil
  ],
  beverages_alcoholic: [
    '1510812431401-41d2bd2722f3', // wine bottles
    '1535958636474-b021ee887b13', // beer
    '1569529465841-dfecdab7503b', // spirits
  ],
  confectionery_snacks: [
    '1481391319762-47dff72954d9', // chocolate
    '1621939514649-280e2ee25f60', // snacks
    '1548907040-4baa42d10919', // candy
  ],
  deli_charcuterie: [
    '1529692236671-f1f6cf9683ba', // charcuterie board
    '1626200419199-3e5b4e9a7c5f', // deli meats
    '1588168333986-5078d3ae3976', // salami
  ],
  condiments_spices: [
    '1596040033229-a9821ebd058d', // spices
    '1532336414036-cf7c87c4f3f8', // condiments
    '1506368249639-73a05d6f6488', // herbs and spices
  ],
  coffee_tea: [
    '1447933601403-0c6688de566e', // coffee beans
    '1495474472287-4d71bcdd2085', // coffee cup
    '1544787219-7f47ccb76574', // tea
  ],
  cleaning_detergents: [
    '1585421514284-652b8c8f71b4', // cleaning supplies
    '1563453392212-326f5e854473', // detergent
    '1584622781867-1c5e52e06d8a', // cleaning products
  ],
  kitchen_utensils_tableware: [
    '1556909114-44e3e70034e3', // kitchen tools
    '1590794056226-79ef935baef1', // tableware
    '1495433324511-bf8e92934d90', // pots and pans
  ],
  horeca_equipment: [
    '1556909172-54557a55fcc7', // commercial kitchen
    '1505275350441-83dcda8eeef5', // restaurant equipment
    '1571624436279-b272aff752b5', // kitchen setup
  ],
  paper_packaging: [
    '1558618666-fcd25c85f82e', // packaging materials
    '1589939705384-5185137a7f0f', // paper products
    '1607344645866-009c320c5ab8', // takeaway packaging
  ],
  personal_care_hygiene: [
    '1556228578-8c89e6adf883', // personal care
    '1571875257727-256c39da42af', // hygiene products
    '1608248543803-ba4f8c70ae0b', // soap and care
  ],
  household_goods: [
    '1556909114-f6e7ad7d3136', // household items
    '1513694203232-719a280e022f', // home goods
    '1558618666-fcd25c85f82e', // household products
  ],
  office_supplies: [
    '1497366216548-37526070297c', // office supplies
    '1586281380349-632531db7ed4', // stationery
    '1456735190827-d1262f71b8a3', // desk supplies
  ],
  electronics_small_appliances: [
    '1518770660439-4636190af475', // electronics
    '1550009158-9ebf69173e03', // small appliances
    '1556656793-08538906a9f8', // gadgets
  ],
};

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

// Metro own brands for badge detection
const METRO_OWN_BRANDS = ['METRO Chef', 'METRO Professional', 'aro', 'Rioba', 'Horeca Select', 'Tarrington House', 'H-Line', 'Sigma'];

function getProductImageUrl(category: string, productId: number): string | null {
  const photos = CATEGORY_PHOTOS[category];
  if (!photos || photos.length === 0) return null;
  const idx = productId % photos.length;
  return `https://images.unsplash.com/photo-${photos[idx]}?w=400&h=400&fit=crop&auto=format&q=80`;
}

export default function ProductCard({ rec, index, onClick }: Props) {
  const [imgError, setImgError] = useState(false);

  // Only percentage and fixed_amount offers directly reduce the shelf price
  const isPriceDiscount = rec.offer_type === 'percentage' || rec.offer_type === 'fixed_amount';

  const discountedPrice = isPriceDiscount
    ? rec.offer_type === 'percentage'
      ? rec.tier1_price * (1 - rec.discount_value / 100)
      : rec.tier1_price - rec.discount_value
    : rec.tier1_price;

  // Only show a % badge when the discounted price is actually lower than shelf price
  const hasDiscount = isPriceDiscount && discountedPrice > 0 && discountedPrice < rec.tier1_price;

  const discountPct = hasDiscount
    ? rec.offer_type === 'percentage'
      ? Math.round(rec.discount_value)
      : Math.round(((rec.tier1_price - discountedPrice) / rec.tier1_price) * 100)
    : 0;

  const netPrice = (hasDiscount ? discountedPrice : rec.tier1_price) / 1.19;

  const bgColor = categoryColors[rec.category] || '#9E9E9E';
  const imageUrl = getProductImageUrl(rec.category, rec.product_id);
  const isOwnBrand = METRO_OWN_BRANDS.some(b => rec.brand.toLowerCase().includes(b.toLowerCase()));

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
          <span className="bg-metro-red text-white text-xs font-bold px-2 py-1 rounded shadow-sm">
            -{discountPct}%
          </span>
        </div>
      )}

      {/* Product image */}
      <div className="relative aspect-square bg-metro-gray-50 overflow-hidden">
        {imageUrl && !imgError ? (
          <img
            src={imageUrl}
            alt={`${rec.brand} ${CATEGORY_DISPLAY[rec.category] || rec.category}`}
            loading="lazy"
            onError={() => setImgError(true)}
            className="product-img w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center p-4">
            <div
              className="w-24 h-24 rounded-xl flex items-center justify-center text-white text-3xl font-bold opacity-80"
              style={{ backgroundColor: bgColor }}
            >
              {(CATEGORY_DISPLAY[rec.category] || rec.category).charAt(0)}
            </div>
          </div>
        )}

        {/* Rank badge */}
        <div className="absolute top-2 right-2 bg-metro-blue/90 text-white text-[10px] font-bold w-6 h-6 rounded-full flex items-center justify-center backdrop-blur-sm">
          #{rec.rank}
        </div>

        {/* Own-brand badge */}
        {isOwnBrand && (
          <div className="absolute bottom-2 left-2 z-10">
            <span className="bg-metro-blue text-white text-[9px] font-semibold px-1.5 py-0.5 rounded backdrop-blur-sm">
              Marca METRO
            </span>
          </div>
        )}
      </div>

      {/* Product info */}
      <div className="p-3">
        {/* Brand */}
        <div className="text-[10px] font-semibold text-metro-blue uppercase tracking-wide mb-0.5">
          {rec.brand}
        </div>

        {/* Product name */}
        <div className="text-sm font-medium text-metro-gray-900 line-clamp-2 min-h-[2.5rem] mb-0.5">
          {rec.brand} {CATEGORY_DISPLAY[rec.category] || rec.category}
        </div>

        {/* Category */}
        <div className="text-xs text-metro-gray-500 mb-1.5">
          {CATEGORY_DISPLAY[rec.category] || rec.category}
        </div>

        {/* Availability */}
        <div className="flex items-center gap-1 mb-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-metro-green" />
          <span className="text-[10px] text-metro-gray-500">disponibil in METRO Cluj</span>
        </div>

        {/* Tier pricing hint */}
        <div className="text-[11px] text-metro-blue font-medium mb-1.5">
          Cumperi mai mult, platesti mai putin
        </div>

        {/* Pricing */}
        <div className="space-y-0">
          {hasDiscount && (
            <div className="text-xs text-metro-gray-400 line-through">
              {rec.tier1_price.toFixed(2)} lei
            </div>
          )}
          <div className="flex items-baseline gap-1">
            <span className="text-lg font-bold text-metro-gray-900 font-heading">
              {hasDiscount ? discountedPrice.toFixed(2) : rec.tier1_price.toFixed(2)}
            </span>
            <span className="text-xs font-medium text-metro-gray-500">lei</span>
          </div>
          <div className="text-[10px] text-metro-gray-400">
            {netPrice.toFixed(2)} lei excl. TVA
          </div>
        </div>

        {/* Offer type badge */}
        <div className="mt-1.5">
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-metro-orange/10 text-metro-orange font-medium">
            {OFFER_TYPE_DISPLAY[rec.offer_type] || rec.offer_type}
          </span>
        </div>
      </div>
    </motion.div>
  );
}
