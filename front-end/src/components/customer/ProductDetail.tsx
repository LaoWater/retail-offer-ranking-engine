import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useProductDetail } from '../../api/hooks';
import type { OfferRecommendation } from '../../types/metro';
import { CATEGORY_DISPLAY, UNIT_TYPE_DISPLAY, OFFER_TYPE_DISPLAY } from '../../types/metro';

interface Props {
  rec: OfferRecommendation | null;
  onClose: () => void;
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

// Use offer_id hash (same as ProductCard) so detail modal shows same photo as the card
function getProductImageUrl(category: string, offerId: number, size = 480): string | null {
  const photos = CATEGORY_PHOTOS[category];
  if (!photos || photos.length === 0) return null;
  const idx = offerId % photos.length;
  return `https://images.unsplash.com/photo-${photos[idx]}?w=${size}&h=${size}&fit=crop&auto=format&q=80`;
}

export default function ProductDetail({ rec, onClose }: Props) {
  const { data: product, isLoading } = useProductDetail(rec?.product_id ?? null);
  const [imgError, setImgError] = useState(false);

  // Reset img error when rec changes — use offer_id (same as ProductCard) for photo consistency
  const imageUrl = rec ? getProductImageUrl(rec.category, rec.offer_id, 480) : null;

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
                    {rec.brand} {rec.subcategory ? rec.subcategory.replace(/_/g, ' ') : CATEGORY_DISPLAY[rec.category] || rec.category}
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
