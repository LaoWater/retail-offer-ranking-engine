import { motion, AnimatePresence } from 'framer-motion';
import { useProductDetail } from '../../api/hooks';
import type { OfferRecommendation } from '../../types/metro';
import { CATEGORY_DISPLAY, UNIT_TYPE_DISPLAY, OFFER_TYPE_DISPLAY } from '../../types/metro';

interface Props {
  rec: OfferRecommendation | null;
  onClose: () => void;
}

export default function ProductDetail({ rec, onClose }: Props) {
  const { data: product, isLoading } = useProductDetail(rec?.product_id ?? null);

  // Recommendation reason
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
              <div className="text-xs text-metro-gray-500 mb-4">
                Pagina principala &gt; {CATEGORY_DISPLAY[rec.category] || rec.category} &gt; {rec.brand}
              </div>

              {/* Product header */}
              <div className="flex flex-col md:flex-row gap-6">
                {/* Image placeholder */}
                <div className="w-full md:w-48 aspect-square bg-metro-gray-50 rounded-xl flex items-center justify-center shrink-0">
                  <div className="text-6xl font-bold text-metro-gray-300">
                    {(CATEGORY_DISPLAY[rec.category] || 'P').charAt(0)}
                  </div>
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
                    <div className="text-xs text-metro-gray-500 mb-3">
                      Cod produs: {product.product_id} | {UNIT_TYPE_DISPLAY[product.unit_type] || product.unit_type}
                    </div>
                  )}

                  {/* Discount badge */}
                  {rec.discount_value > 0 && (
                    <span className="inline-block bg-metro-red text-white text-sm font-bold px-3 py-1 rounded mb-3">
                      -{rec.offer_type === 'percentage' ? Math.round(rec.discount_value) : Math.round((rec.discount_value / rec.tier1_price) * 100)}% Reducere
                    </span>
                  )}

                  {/* Availability */}
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-2.5 h-2.5 rounded-full bg-metro-green" />
                    <span className="text-sm text-metro-gray-700">disponibil in METRO Cluj</span>
                  </div>

                  {/* ML Insight */}
                  <div className="bg-metro-blue/5 rounded-lg p-3 mb-4">
                    <div className="flex items-center gap-2 mb-2">
                      <svg className="w-4 h-4 text-metro-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      <span className="text-xs font-medium text-metro-blue">Insight ML</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="flex-1 bg-metro-gray-200 rounded-full h-2">
                        <div
                          className="bg-metro-blue rounded-full h-2 transition-all"
                          style={{ width: `${rec.score * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-semibold text-metro-blue">{(rec.score * 100).toFixed(1)}%</span>
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
                        <tr className="border-t border-metro-gray-100">
                          <td className="px-4 py-3 text-metro-gray-900">
                            1 {UNIT_TYPE_DISPLAY[product.unit_type] || product.unit_type}
                          </td>
                          <td className="px-4 py-3 text-right font-semibold text-metro-gray-900">
                            {product.tier1_price.toFixed(2)} RON
                          </td>
                          <td className="px-4 py-3 text-right text-metro-gray-400">-</td>
                        </tr>

                        {/* Tier 2 */}
                        {product.tier2_price && product.tier2_min_qty && (
                          <tr className="border-t border-metro-gray-100 bg-metro-blue/3">
                            <td className="px-4 py-3 text-metro-blue font-medium">
                              {product.tier2_min_qty}+ {UNIT_TYPE_DISPLAY[product.unit_type] || product.unit_type}
                            </td>
                            <td className="px-4 py-3 text-right font-bold text-metro-blue">
                              {product.tier2_price.toFixed(2)} RON
                            </td>
                            <td className="px-4 py-3 text-right text-metro-green font-medium">
                              -{Math.round((1 - product.tier2_price / product.tier1_price) * 100)}%
                            </td>
                          </tr>
                        )}

                        {/* Tier 3 */}
                        {product.tier3_price && product.tier3_min_qty && (
                          <tr className="border-t border-metro-gray-100 bg-metro-blue/5">
                            <td className="px-4 py-3 text-metro-blue font-bold">
                              {product.tier3_min_qty}+ {UNIT_TYPE_DISPLAY[product.unit_type] || product.unit_type}
                            </td>
                            <td className="px-4 py-3 text-right font-bold text-metro-blue">
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
                  <div className="text-sm font-semibold">{rec.expiry_date}</div>
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
