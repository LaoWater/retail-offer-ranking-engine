import { useState } from 'react';
import { motion } from 'framer-motion';
import type { OfferRecommendation } from '../../types/metro';
import { CATEGORY_DISPLAY, OFFER_TYPE_DISPLAY } from '../../types/metro';

interface Props {
  rec: OfferRecommendation;
  index: number;
  onClick: () => void;
}

// Curated Unsplash photo IDs per category — 8 per category, all verified working
const CATEGORY_PHOTOS: Record<string, string[]> = {
  meat_poultry: [
    '1708974140638-8554bc01690d', '1733700469173-15d46efc2c09', '1608502735811-0affbb61f260',
    '1600180786489-2e9a5b4041b5', '1583549323189-5a3335634f4e', '1630684789587-9a2188a92bbf',
    '1592877186734-6e558cf0dfaf', '1682334005022-619f67527772',
  ],
  seafood: [
    '1758384075930-6e3835d22b1d', '1763093226729-b412ad2f309d', '1696425238816-60797dd15272',
    '1633244092662-82acaf20bd4f', '1548587468-971ebe4c8c3b', '1741728981109-8f9e682cbefd',
    '1748836043840-8fd707af5046', '1603894483228-9a3d10c32390',
  ],
  dairy_eggs: [
    '1686998424991-201e0c94f6a4', '1686998424326-8d9dad7aac94', '1686998424326-d3ca77fe02fc',
    '1736752346246-61f4daedfde0', '1686998424941-9006770e7f3e', '1686998424979-cfc089e79d92',
    '1686998423980-ab223d183055', '1633893215271-f7e1fca081ad',
  ],
  fruits_vegetables: [
    '1700064165267-8fa68ef07167', '1595303477117-8dddd2894299', '1645931413394-01bd95d294ca',
    '1568581789190-ae90a7da930b', '1672075805860-f621fdc0c396', '1618254676841-71055a17efc2',
    '1594567168326-3e0e6ff869f4', '1620249784068-46499a3bcdc0',
  ],
  beverages_non_alcoholic: [
    '1654245836977-a1d1a2a91859', '1616118132534-381148898bb4', '1727233431893-e38a524d7f4b',
    '1624392294437-8fc9f876f4d3', '1644929848364-cca2fbd64159', '1698047558063-54c2ec25e936',
    '1722239311810-86fda1346414', '1606873088303-9a23efba7ab9',
  ],
  bakery_pastry: [
    '1762117863153-6db91d93eb66', '1770650195496-f8b577782ca3', '1769615020959-8a17bd77e849',
    '1737065175923-7b05466a2c1a', '1733210438254-46772630092f', '1737092684892-c82937fc072a',
    '1652288032806-6887695e6424', '1628697639527-e370a51de205',
  ],
  frozen_foods: [
    '1749524504630-9a812e20925a', '1766237167270-a3a28e45c710', '1764350275753-a01b4cb8fe33',
    '1494878354154-772d013c9a26', '1764981965949-96bbe4e7eebe', '1764337008605-44abfb0f3816',
    '1570557237290-0f3a3dfd917c', '1763968208727-8e8c6d6e13b0',
  ],
  grocery_staples: [
    '1594326120744-7fac86ea96c4', '1649777476920-0eef34169cdb', '1602016753529-c0f1bc90b98b',
    '1513553016575-0ccd93e15315', '1733700469181-fc8edf9af33f', '1642761712600-2fa6e0837577',
    '1612774672714-9b4a0a128886', '1601387434127-20979856e76e',
  ],
  beverages_alcoholic: [
    '1610826906052-379178e79d9d', '1744059718694-6d62a537fedc', '1594076119274-d57a733b02f8',
    '1756716918459-d4643d262514', '1651945496833-1308066c48ec', '1733075610745-df8df93a78fe',
    '1601816147275-f7f9f876f4bc', '1533164575821-85693fa5febc',
  ],
  confectionery_snacks: [
    '1627373369962-42fd4fde6504', '1702744217602-c93a922b7c59', '1649678948436-12aff596159d',
    '1729875750157-2a01cd39b1cc', '1702744217859-ae55b0a49687', '1702744217978-233e3cfd92ca',
    '1624708363456-99f41f1c3fc8', '1702313040371-6cde8b0f1972',
  ],
  deli_charcuterie: [
    '1739785938354-1a7bb4dae625', '1600180786608-28d06391d25c', '1635502070904-2c8d31dd9c83',
    '1564812003529-ef126e9b5d7c', '1534432541771-9f2f5cfd1c15', '1669622997855-486667924955',
    '1746718547546-7111b8cc3f7a', '1769772619357-216a3085f718',
  ],
  condiments_spices: [
    '1634114627043-9a2abf455494', '1489841060824-0f3119e26686', '1719505503086-504338bad126',
    '1472721457610-d040f398d2fa', '1666269013368-41ba9ca95958', '1749800816385-b98700ea51da',
    '1637683085083-fa760c1fd0af', '1570284042036-b985e6bdcc17',
  ],
  coffee_tea: [
    '1587985782608-20062892559d', '1605170512248-d03f7f10b168', '1688624535804-7f31e358b66b',
    '1634250497145-101badd1d75c', '1657816652393-85affc01636f', '1519929676140-1384fc9052d4',
    '1625862956024-13240fd52e7a', '1634993073618-5312c9781162',
  ],
  cleaning_detergents: [
    '1610245556402-6432cee51c47', '1669738540556-dfbd7099c9eb', '1624372635310-01d078c05dd9',
    '1584813470613-5b1c1cad3d69', '1722842253242-1a40ba701095', '1623008548370-90e908279959',
    '1585421514284-efb74c2b69ba', '1683559086021-7f5e3b5e11cb',
  ],
  kitchen_utensils_tableware: [
    '1603899885801-b25efec31f63', '1547978074-bf0b7285d686', '1612293905904-d45b1e5d0960',
    '1760269734155-b6bb8c41dad6', '1716545367002-69c4e90b81d9', '1743684456567-a3d32dbf702e',
    '1581442330928-a4189fd7ef57', '1674660346036-4b3df3f07cca',
  ],
  horeca_equipment: [
    '1589109807644-924edf14ee09', '1708915965975-2a950db0e215', '1762329924239-e204f101fca4',
    '1768321611024-39d91399abaf', '1769456455600-9aa2441a0fcd', '1759873360996-3f165ebc8aae',
    '1762922425168-616c0d654a75', '1765230182369-4940d69e6811',
  ],
  paper_packaging: [
    '1769355104335-acef3aa4c9b6', '1631010231888-777b6285ef84', '1631010231130-5c7828d9a3a7',
    '1575833947349-69324d765146', '1696764190851-576190638b60', '1759420347222-e727ac840ad9',
    '1573376671096-e1fce2d1f19d', '1630448927918-1dbcd8ba439b',
  ],
  personal_care_hygiene: [
    '1658684860796-b52128d5bdd6', '1590928192338-73e004fad28e', '1674632689991-d8e98f0fba50',
    '1584744982491-665216d95f8b', '1689893265427-d7da200eff05', '1750271336429-8b0a507785c0',
    '1712482937664-5697b56ed6f1', '1721274503142-63af7aa9c1ad',
  ],
  household_goods: [
    '1724847885015-be191f1a47ef', '1692576855758-318a1fa8ff6d', '1769956482474-b855b8c293a4',
    '1625931046289-e51edea3e176', '1691057183096-16172f811638', '1596748176765-08c3a6c9969a',
    '1610701595970-a2a04cafb6f5', '1737065183310-aef762bd011c',
  ],
  office_supplies: [
    '1562093890-37ee6fe41521', '1722929025573-3d461531ac4d', '1565530623098-9f74c84d7f71',
    '1607522783211-cb0d1ffdab8a', '1617178965617-45772e37b57d', '1568572363041-b6ac91a710e7',
    '1617178964562-bccdf0b5464a', '1722929309984-c6b3e55dd6e5',
  ],
  electronics_small_appliances: [
    '1738898101611-2a9a3d4c75b5', '1670905901357-0cb2e51bfe38', '1578845425669-b6562f83b11e',
    '1696353558013-16b18d8c1640', '1740803292349-c7e53f7125b2', '1655354438845-561bc349a1a4',
    '1740046702830-d379ee39890e', '1548989740-57e34f4d9a18',
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
