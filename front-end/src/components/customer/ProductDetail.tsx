import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useProductDetail } from '../../api/hooks';
import type { OfferRecommendation } from '../../types/metro';
import { CATEGORY_DISPLAY, UNIT_TYPE_DISPLAY, OFFER_TYPE_DISPLAY } from '../../types/metro';

interface Props {
  rec: OfferRecommendation | null;
  onClose: () => void;
}

// Same curated photo IDs as ProductCard — keep in sync
const CATEGORY_PHOTOS: Record<string, string[]> = {
  meat_poultry: ['1607623814825-11cdae563a3d', '1602473812024-4708fa8c1be1', '1588347818481-07a913c1d8b7'],
  seafood: ['1534604973900-c43ab4c2e0ab', '1559709319-3e3fcaa3ed1b', '1615141982883-c7ad0e69fd62'],
  dairy_eggs: ['1628088062854-d1870b4553da', '1559598467-f8b76c8155d0', '1582722872445-44dc5f7e3c8f'],
  fruits_vegetables: ['1610832958506-c8b927c2b8ff', '1597714026720-8f55c1a5e6d3', '1540420773420-3366772f4999'],
  beverages_non_alcoholic: ['1544145945-f90425340c7e', '1556679343-c7306c1976bc', '1625772299848-391b6a87d7b3'],
  bakery_pastry: ['1509440159596-0249088772ff', '1517433670267-08bbd4be890f', '1555507036-ab1f4038024a'],
  frozen_foods: ['1584568694244-14fbdf83bd30', '1563805042-7684c019e1cb', '1488477181946-6428a0291777'],
  grocery_staples: ['1586201375761-83865001e31c', '1556909114-f6e7ad7d3136', '1620706857370-e1b9770e8bb1'],
  beverages_alcoholic: ['1510812431401-41d2bd2722f3', '1535958636474-b021ee887b13', '1569529465841-dfecdab7503b'],
  confectionery_snacks: ['1481391319762-47dff72954d9', '1621939514649-280e2ee25f60', '1548907040-4baa42d10919'],
  deli_charcuterie: ['1529692236671-f1f6cf9683ba', '1626200419199-3e5b4e9a7c5f', '1588168333986-5078d3ae3976'],
  condiments_spices: ['1596040033229-a9821ebd058d', '1532336414036-cf7c87c4f3f8', '1506368249639-73a05d6f6488'],
  coffee_tea: ['1447933601403-0c6688de566e', '1495474472287-4d71bcdd2085', '1544787219-7f47ccb76574'],
  cleaning_detergents: ['1585421514284-652b8c8f71b4', '1563453392212-326f5e854473', '1584622781867-1c5e52e06d8a'],
  kitchen_utensils_tableware: ['1556909114-44e3e70034e3', '1590794056226-79ef935baef1', '1495433324511-bf8e92934d90'],
  horeca_equipment: ['1556909172-54557a55fcc7', '1505275350441-83dcda8eeef5', '1571624436279-b272aff752b5'],
  paper_packaging: ['1558618666-fcd25c85f82e', '1589939705384-5185137a7f0f', '1607344645866-009c320c5ab8'],
  personal_care_hygiene: ['1556228578-8c89e6adf883', '1571875257727-256c39da42af', '1608248543803-ba4f8c70ae0b'],
  household_goods: ['1556909114-f6e7ad7d3136', '1513694203232-719a280e022f', '1558618666-fcd25c85f82e'],
  office_supplies: ['1497366216548-37526070297c', '1586281380349-632531db7ed4', '1456735190827-d1262f71b8a3'],
  electronics_small_appliances: ['1518770660439-4636190af475', '1550009158-9ebf69173e03', '1556656793-08538906a9f8'],
};

function getProductImageUrl(category: string, productId: number, size = 480): string | null {
  const photos = CATEGORY_PHOTOS[category];
  if (!photos || photos.length === 0) return null;
  const idx = productId % photos.length;
  return `https://images.unsplash.com/photo-${photos[idx]}?w=${size}&h=${size}&fit=crop&auto=format&q=80`;
}

export default function ProductDetail({ rec, onClose }: Props) {
  const { data: product, isLoading } = useProductDetail(rec?.product_id ?? null);
  const [imgError, setImgError] = useState(false);

  // Reset img error when rec changes
  const imageUrl = rec ? getProductImageUrl(rec.category, rec.product_id, 480) : null;

  const getReasonText = (rec: OfferRecommendation) => {
    if (rec.score > 0.8) return 'Recomandat special pentru afacerea ta';
    if (rec.campaign_type === 'personalized') return 'Bazat pe preferintele tale de categorie';
    if (rec.campaign_type === 'weekly_catalog') return 'Din catalogul saptamanii';
    return 'Popular printre clientii METRO';
  };

  return (
    <AnimatePresence>
      {rec && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/40 z-50"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed bottom-0 left-0 right-0 z-50 bg-white rounded-t-3xl max-h-[85vh] overflow-y-auto"
          >
            {/* Handle */}
            <div className="sticky top-0 bg-white pt-3 pb-2 flex justify-center rounded-t-3xl">
              <div className="w-10 h-1 rounded-full bg-metro-gray-300" />
            </div>

            <div className="px-6 pb-8">
              {/* Close button */}
              <button
                onClick={onClose}
                className="absolute top-4 right-4 w-8 h-8 rounded-full bg-metro-gray-100 flex items-center justify-center hover:bg-metro-gray-200 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>

              {/* Breadcrumb */}
              <div className="text-xs text-metro-gray-500 mb-4 flex items-center gap-1.5">
                <span>Pagina principala</span>
                <svg className="w-3 h-3 text-metro-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                <span>{CATEGORY_DISPLAY[rec.category] || rec.category}</span>
                <svg className="w-3 h-3 text-metro-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                <span className="text-metro-gray-700 font-medium">{rec.brand}</span>
              </div>

              {/* Product header */}
              <div className="flex flex-col md:flex-row gap-6">
                {/* Image */}
                <div className="w-full md:w-48 aspect-square bg-metro-gray-50 rounded-xl overflow-hidden shrink-0">
                  {imageUrl && !imgError ? (
                    <img
                      src={imageUrl}
                      alt={`${rec.brand} ${CATEGORY_DISPLAY[rec.category] || rec.category}`}
                      loading="lazy"
                      onError={() => setImgError(true)}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <div className="text-6xl font-bold text-metro-gray-300">
                        {(CATEGORY_DISPLAY[rec.category] || 'P').charAt(0)}
                      </div>
                    </div>
                  )}
                </div>

                {/* Info */}
                <div className="flex-1">
                  {/* Brand */}
                  <div className="text-xs font-semibold text-metro-blue uppercase tracking-wider mb-1">
                    {rec.brand}
                  </div>

                  {/* Name */}
                  <h3 className="text-xl font-bold text-metro-gray-900 mb-2">
                    {rec.brand} {CATEGORY_DISPLAY[rec.category] || rec.category}
                  </h3>

                  {/* Product code */}
                  {product && (
                    <div className="text-xs text-metro-gray-500 mb-3 font-mono">
                      Cod produs: {product.product_id} | {UNIT_TYPE_DISPLAY[product.unit_type] || product.unit_type}
                    </div>
                  )}

                  {/* Discount badge — only for offer types that directly reduce the shelf price */}
                  {(rec.offer_type === 'percentage' || rec.offer_type === 'fixed_amount') && rec.discount_value > 0 && (() => {
                    const discPct = rec.offer_type === 'percentage'
                      ? Math.round(rec.discount_value)
                      : Math.round((rec.discount_value / rec.tier1_price) * 100);
                    const discPrice = rec.offer_type === 'percentage'
                      ? rec.tier1_price * (1 - rec.discount_value / 100)
                      : rec.tier1_price - rec.discount_value;
                    return discPrice > 0 && discPct > 0 ? (
                      <span className="inline-block bg-metro-red text-white text-sm font-bold px-3 py-1 rounded mb-3">
                        -{discPct}% Reducere
                      </span>
                    ) : null;
                  })()}

                  {/* Availability */}
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-2.5 h-2.5 rounded-full bg-metro-green" />
                    <span className="text-sm text-metro-gray-700">disponibil in METRO Cluj</span>
                  </div>

                  {/* ML Insight */}
                  <div className="bg-metro-blue/5 rounded-lg p-3 mb-4 border border-metro-blue/10">
                    <div className="flex items-center gap-2 mb-2">
                      <svg className="w-4 h-4 text-metro-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      <span className="text-xs font-semibold text-metro-blue font-heading">Insight ML</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="flex-1 bg-metro-gray-200 rounded-full h-2 overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${rec.score * 100}%` }}
                          transition={{ duration: 0.8, ease: 'easeOut' }}
                          className="bg-gradient-to-r from-metro-blue to-metro-blue-light rounded-full h-2"
                        />
                      </div>
                      <span className="text-sm font-bold text-metro-blue font-mono">{(rec.score * 100).toFixed(1)}%</span>
                    </div>
                    <p className="text-xs text-metro-gray-600 mt-1">{getReasonText(rec)}</p>
                  </div>
                </div>
              </div>

              {/* Tier pricing table */}
              {product && (
                <div className="mt-6">
                  <h4 className="text-sm font-bold text-metro-gray-900 mb-3">
                    Cumperi mai mult, platesti mai putin
                  </h4>
                  <div className="border border-metro-gray-200 rounded-xl overflow-hidden">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-metro-gray-50">
                          <th className="text-left px-4 py-3 font-semibold text-metro-gray-700">Cantitate</th>
                          <th className="text-right px-4 py-3 font-semibold text-metro-gray-700">Pret/unitate (incl. TVA)</th>
                          <th className="text-right px-4 py-3 font-semibold text-metro-gray-700">Economie</th>
                        </tr>
                      </thead>
                      <tbody>
                        {/* Tier 1 */}
                        <tr className="border-t border-metro-gray-100 hover:bg-metro-gray-50/50 transition-colors">
                          <td className="px-4 py-3 text-metro-gray-900">
                            1 {UNIT_TYPE_DISPLAY[product.unit_type] || product.unit_type}
                          </td>
                          <td className="px-4 py-3 text-right font-semibold text-metro-gray-900 font-mono">
                            {product.tier1_price.toFixed(2)} RON
                          </td>
                          <td className="px-4 py-3 text-right text-metro-gray-400">-</td>
                        </tr>

                        {/* Tier 2 */}
                        {product.tier2_price && product.tier2_min_qty && (
                          <tr className="border-t border-metro-gray-100 bg-metro-blue/3 hover:bg-metro-blue/5 transition-colors">
                            <td className="px-4 py-3 text-metro-blue font-medium">
                              {product.tier2_min_qty}+ {UNIT_TYPE_DISPLAY[product.unit_type] || product.unit_type}
                            </td>
                            <td className="px-4 py-3 text-right font-bold text-metro-blue font-mono">
                              {product.tier2_price.toFixed(2)} RON
                            </td>
                            <td className="px-4 py-3 text-right text-metro-green font-medium">
                              -{Math.round((1 - product.tier2_price / product.tier1_price) * 100)}%
                            </td>
                          </tr>
                        )}

                        {/* Tier 3 — best price, accented */}
                        {product.tier3_price && product.tier3_min_qty && (
                          <tr className="border-t border-metro-gray-100 bg-metro-blue/5 hover:bg-metro-blue/8 transition-colors border-l-4 border-l-metro-yellow">
                            <td className="px-4 py-3 text-metro-blue font-bold">
                              {product.tier3_min_qty}+ {UNIT_TYPE_DISPLAY[product.unit_type] || product.unit_type}
                            </td>
                            <td className="px-4 py-3 text-right font-bold text-metro-blue font-mono text-base">
                              {product.tier3_price.toFixed(2)} RON
                            </td>
                            <td className="px-4 py-3 text-right text-metro-green font-bold">
                              -{Math.round((1 - product.tier3_price / product.tier1_price) * 100)}%
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Offer details */}
              <div className="mt-6 grid grid-cols-2 gap-3">
                <div className="bg-metro-gray-50 rounded-xl p-4">
                  <div className="text-xs text-metro-gray-500 mb-1">Tip oferta</div>
                  <div className="text-sm font-semibold">{OFFER_TYPE_DISPLAY[rec.offer_type] || rec.offer_type}</div>
                </div>
                <div className="bg-metro-gray-50 rounded-xl p-4">
                  <div className="text-xs text-metro-gray-500 mb-1">Valabilitate</div>
                  <div className="text-sm font-semibold font-mono">{rec.expiry_date}</div>
                </div>
                {rec.campaign_type && (
                  <div className="bg-metro-gray-50 rounded-xl p-4">
                    <div className="text-xs text-metro-gray-500 mb-1">Campanie</div>
                    <div className="text-sm font-semibold">{rec.campaign_type.replace(/_/g, ' ')}</div>
                  </div>
                )}
                <div className="bg-metro-gray-50 rounded-xl p-4">
                  <div className="text-xs text-metro-gray-500 mb-1">Categorie</div>
                  <div className="text-sm font-semibold">{CATEGORY_DISPLAY[rec.category] || rec.category}</div>
                </div>
              </div>

              {/* Product details */}
              {product && !isLoading && (
                <div className="mt-6">
                  <h4 className="text-sm font-bold text-metro-gray-900 mb-3">Detalii produs</h4>
                  <div className="text-sm text-metro-gray-700 space-y-2">
                    {product.subcategory && (
                      <div className="flex justify-between">
                        <span className="text-metro-gray-500">Subcategorie</span>
                        <span>{product.subcategory.replace(/_/g, ' ')}</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span className="text-metro-gray-500">Marca proprie</span>
                      <span>{product.is_own_brand ? (product.own_brand_name || 'Da') : 'Nu'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-metro-gray-500">Valabilitate</span>
                      <span>{product.shelf_life_days} zile</span>
                    </div>
                    {product.is_daily_price && (
                      <div className="flex justify-between">
                        <span className="text-metro-gray-500">Pret zilnic (Tagespreis)</span>
                        <span className="text-metro-orange font-medium">Da</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Add to list button */}
              <button className="w-full mt-6 bg-metro-blue text-white py-3 rounded-xl font-semibold hover:bg-metro-blue-dark transition-colors">
                Adauga articole in lista
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
