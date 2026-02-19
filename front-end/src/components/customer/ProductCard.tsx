import { useState } from 'react';
import { motion } from 'framer-motion';
import type { OfferRecommendation } from '../../types/metro';
import { CATEGORY_DISPLAY, OFFER_TYPE_DISPLAY } from '../../types/metro';

interface Props {
  rec: OfferRecommendation;
  index: number;
  onClick: () => void;
}

// Curated Unsplash photo IDs per category — 8 per category for variety
const CATEGORY_PHOTOS: Record<string, string[]> = {
  meat_poultry: [
    '1607623814825-11cdae563a3d', // raw steak
    '1602473812024-4708fa8c1be1', // butcher meat
    '1588347818481-07a913c1d8b7', // chicken
    '1529694157872-4c80f8dc2b57', // pork chops
    '1544025162-d76538976022', // ground beef
    '1615141982883-c7ad0e69fd62', // meat cuts
    '1518492250015-ce5de7900e94', // lamb rack
    '1504674900247-0877df9cc836', // grilled meat
  ],
  seafood: [
    '1534604973900-c43ab4c2e0ab', // fish market
    '1559709319-3e3fcaa3ed1b', // fresh fish
    '1615141982883-c7ad0e69fd62', // salmon fillet
    '1519708227418-a2f521dbe451', // shrimp
    '1571167366873-80d55a02ba67', // seafood platter
    '1498654077880-f760b6b25d18', // tuna
    '1565680018434-b513d5e5fd47', // oysters
    '1576584879939-7670c17b4b91', // crab
  ],
  dairy_eggs: [
    '1628088062854-d1870b4553da', // cheese assortment
    '1559598467-f8b76c8155d0', // milk
    '1582722872445-44dc5f7e3c8f', // eggs
    '1486297671463-8f37c5b7fd52', // butter
    '1550583724-b2692b85b150', // yogurt
    '1559598467-f8b76c8155d0', // dairy
    '1589187151525-0b3c6f8e1bac', // cheese wheel
    '1542051841857-5f90071e7989', // fresh milk
  ],
  fruits_vegetables: [
    '1610832958506-c8b927c2b8ff', // fresh vegetables
    '1597714026720-8f55c1a5e6d3', // fruits
    '1540420773420-3366772f4999', // colorful veggies
    '1518977676112-2c0f7f2d1e59', // tomatoes
    '1550258987-190a2d41a8ba', // salad greens
    '1464965723986-5b5ecfd3eb70', // peppers
    '1483392552503-8d99f5e5f09e', // mushrooms
    '1574316243850-ca484f2abae3', // potatoes
  ],
  beverages_non_alcoholic: [
    '1544145945-f90425340c7e', // water bottles
    '1556679343-c7306c1976bc', // juice
    '1625772299848-391b6a87d7b3', // soft drinks
    '1495474472287-4d71bcdd2085', // coffee
    '1558618666-fcd25c85f82e', // cans
    '1571167530149-c12e028dda9c', // energy drink
    '1500530855697-b586d89ba3ee', // mineral water
    '1534353436294-0dbd4bdac845', // smoothie
  ],
  bakery_pastry: [
    '1509440159596-0249088772ff', // fresh bread
    '1517433670267-08bbd4be890f', // pastries
    '1555507036-ab1f4038024a', // baked goods
    '1565958011814-3912084e8a47', // croissants
    '1589647363585-f4a7d3a1cfc5', // rolls
    '1549931319-a545dcf3bc73', // cake
    '1558961363-fa8fdf82db35', // baguette
    '1486887735655-a76e50e8b847', // muffins
  ],
  frozen_foods: [
    '1584568694244-14fbdf83bd30', // frozen vegetables
    '1563805042-7684c019e1cb', // frozen aisle
    '1488477181946-6428a0291777', // ice cream
    '1571167366873-80d55a02ba67', // frozen fish
    '1547592180-85f173990554', // frozen pizza
    '1606914469633-4c7e8d14e2e0', // frozen meals
    '1608897013039-887f21d8c804', // peas frozen
    '1548781268-ebf4f5e8c3d8', // frozen berries
  ],
  grocery_staples: [
    '1586201375761-83865001e31c', // pasta
    '1556909114-f6e7ad7d3136', // rice
    '1620706857370-e1b9770e8bb1', // cooking oil
    '1574323347407-f2f06d5c48a5', // flour
    '1610348347260-6e17c5e3b8f2', // canned goods
    '1532550884805-0c0b51b3cf66', // sugar
    '1504478591226-ebf4ef6b4fbc', // salt and spices
    '1606140778520-c4c8c0f8c4e0', // lentils
  ],
  beverages_alcoholic: [
    '1510812431401-41d2bd2722f3', // wine bottles
    '1535958636474-b021ee887b13', // beer
    '1569529465841-dfecdab7503b', // spirits
    '1558617853-acdf0ff54f1c', // whiskey
    '1566633806-83bb088e8d3a', // champagne
    '1474722883778-792e7990302f', // red wine
    '1501605780225-27d83310a7c6', // beer tap
    '1527866959879-e0a14e6ee4f0', // gin bottle
  ],
  confectionery_snacks: [
    '1481391319762-47dff72954d9', // chocolate
    '1621939514649-280e2ee25f60', // snacks
    '1548907040-4baa42d10919', // candy
    '1606312619070-d48b8e3c9d94', // chips
    '1614065745399-43b7dbbb7e10', // cookies
    '1559181567-c3190592a949', // gummy bears
    '1553979459-d1b5a8b44c68', // mixed nuts
    '1571506955785-f4cb1a8a6d1f', // popcorn
  ],
  deli_charcuterie: [
    '1529692236671-f1f6cf9683ba', // charcuterie board
    '1588168333986-5078d3ae3976', // salami
    '1578020818892-9f54e15a0f8e', // ham
    '1615461066841-6116e61058f4', // prosciutto
    '1567360425442-93ea5cb4de1f', // cold cuts
    '1559757148-5c350d0d3c56', // cured meats
    '1579871494447-9811cf80d66c', // smoked salmon
    '1547592166-23ac45744acd', // olives & pickles
  ],
  condiments_spices: [
    '1596040033229-a9821ebd058d', // spices
    '1532336414036-cf7c87c4f3f8', // condiments
    '1506368249639-73a05d6f6488', // herbs
    '1508615039623-a25605d2b022', // mustard
    '1604152135947-50bddeec0b04', // ketchup
    '1571167530149-c12e028dda9c', // sauces
    '1573225342350-16731dd9bf3d', // olive oil
    '1531315396756-905d68d21b56', // vinegar
  ],
  coffee_tea: [
    '1447933601403-0c6688de566e', // coffee beans
    '1495474472287-4d71bcdd2085', // coffee cup
    '1544787219-7f47ccb76574', // tea
    '1509042239860-f550ce710b93', // espresso
    '1461023058943-07fcbe16d735', // latte art
    '1576092768241-dec231879fc3', // cappuccino
    '1564890369478-c89ca6d9cde9', // green tea
    '1497515114865-36b57a301b18', // tea leaves
  ],
  cleaning_detergents: [
    '1585421514284-652b8c8f71b4', // cleaning supplies
    '1563453392212-326f5e854473', // detergent
    '1584622781867-1c5e52e06d8a', // cleaning products
    '1558769124-e7c25f5af3be', // spray bottle
    '1604187351574-42e8a0e3c0e4', // mop bucket
    '1589820276791-14b22a71a01f', // disinfectant
    '1571171071994-8d5a8e2b8b5d', // sponge
    '1567219012049-b7de2bb42bac', // laundry pods
  ],
  kitchen_utensils_tableware: [
    '1556909114-44e3e70034e3', // kitchen tools
    '1590794056226-79ef935baef1', // tableware
    '1495433324511-bf8e92934d90', // pots and pans
    '1584990347209-6bbb8e4fa57b', // knife set
    '1519125323398-675f0ddb6308', // plates
    '1581401100143-b4f5f2bc1c22', // cutting board
    '1608198093002-ad4e005484ec', // wine glasses
    '1567306226416-28f0efdc88ce', // cooking utensils
  ],
  horeca_equipment: [
    '1556909172-54557a55fcc7', // commercial kitchen
    '1505275350441-83dcda8eeef5', // restaurant equipment
    '1571624436279-b272aff752b5', // kitchen setup
    '1414235077428-338989a2e8c0', // professional oven
    '1466637574441-749b8f19452f', // refrigerator unit
    '1584438784894-089d6a62b8fa', // display case
    '1566073787955-309a13fb98e5', // food warmer
    '1559329255-07bf3e8b56b9', // coffee machine
  ],
  paper_packaging: [
    '1558618666-fcd25c85f82e', // packaging
    '1589939705384-5185137a7f0f', // paper products
    '1607344645866-009c320c5ab8', // takeaway
    '1530026405845-83c240810dd2', // boxes
    '1567016432779-094069958ea5', // napkins
    '1574634291555-3c0a2c29ced7', // bags
    '1531492746076-161ca9bcad58', // cling wrap
    '1571167530149-c12e028dda9c', // foil
  ],
  personal_care_hygiene: [
    '1556228578-8c89e6adf883', // personal care
    '1571875257727-256c39da42af', // hygiene
    '1608248543803-ba4f8c70ae0b', // soap
    '1540555700478-4be290a3d798', // shampoo
    '1526947425960-945c6e72858f', // toothbrush
    '1576426863890-b9edfe0d9f26', // skincare
    '1512290923902-8a9f81dc236c', // hand sanitizer
    '1607705407673-57cdb73e0b4a', // deodorant
  ],
  household_goods: [
    '1513694203232-719a280e022f', // home goods
    '1558769124-e7c25f5af3be', // storage
    '1556909114-f6e7ad7d3136', // household
    '1578662996442-48f60103fc96', // apron
    '1493663284031-b7e3aaa64c4b', // table linen
    '1586105251261-72a756497a11', // baskets
    '1560185007-c5ca9d2c014d', // towels
    '1571167530149-c12e028dda9c', // gloves
  ],
  office_supplies: [
    '1497366216548-37526070297c', // office supplies
    '1586281380349-632531db7ed4', // stationery
    '1456735190827-d1262f71b8a3', // desk
    '1587307092704-4d0c45e965a9', // notebooks
    '1583485088034-697b5bc54ccd', // pens
    '1568219656418-15c7abb80a72', // printer paper
    '1503676260728-1c00da094a0b', // folders
    '1572521165328-1b8a4d8ac3e7', // tape
  ],
  electronics_small_appliances: [
    '1518770660439-4636190af475', // electronics
    '1550009158-9ebf69173e03', // small appliances
    '1556656793-08538906a9f8', // gadgets
    '1574944985070-8f3ebc6b79d2', // coffee maker
    '1585771724684-38269d6639fd', // blender
    '1531746790731-6c087fecd65a', // microwave
    '1593359677879-a26632437684', // scale
    '1558618666-fcd25c85f82e', // kitchen electric
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

// Known real brand names — anything else is a synthetic slug and should be cleaned
const KNOWN_BRANDS = new Set([
  'METRO Chef', 'METRO Professional', 'aro', 'Rioba', 'Horeca Select',
  'Tarrington House', 'H-Line', 'Sigma',
  'Borsec', 'Dorna', 'Bucovina', 'Ursus', 'Timisoreana', 'Bergenbier',
  'Heidi', 'ROM', 'Joe', 'Poiana',
]);

function cleanBrandName(raw: string): string {
  // If it already looks like a real brand, return as-is
  for (const b of KNOWN_BRANDS) {
    if (raw.toLowerCase().includes(b.toLowerCase())) return b;
  }
  // Strip category prefix pattern: "meat_poultry_brand_7" → "Brand 7"
  // Pattern: word_word_brand_N  OR  word_brand_N
  const m = raw.match(/brand[_\s](\d+)$/i);
  if (m) return `Brand ${m[1]}`;
  // Generic cleanup: replace underscores, title-case
  return raw.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function cleanProductName(brand: string, subcategory: string | null, category: string): string {
  const cleanedBrand = cleanBrandName(brand);
  const subcatLabel = subcategory
    ? subcategory.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
    : CATEGORY_DISPLAY[category] || category.replace(/_/g, ' ');
  return `${cleanedBrand} — ${subcatLabel}`;
}

// Use offer_id (unique per recommendation card) so no two cards share the same photo
function getProductImageUrl(category: string, offerId: number): string | null {
  const photos = CATEGORY_PHOTOS[category];
  if (!photos || photos.length === 0) return null;
  const idx = offerId % photos.length;
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
  const imageUrl = getProductImageUrl(rec.category, rec.offer_id);
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
          {cleanBrandName(rec.brand)}
        </div>

        {/* Product name */}
        <div className="text-sm font-medium text-metro-gray-900 line-clamp-2 min-h-[2.5rem] mb-0.5">
          {cleanProductName(rec.brand, rec.subcategory, rec.category)}
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
