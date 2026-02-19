import { motion } from 'framer-motion';
import { useBehaviorSummary } from '../../api/hooks';
import { CATEGORY_DISPLAY, BUSINESS_TYPE_DISPLAY } from '../../types/metro';

const SEGMENT_COLORS: Record<string, string> = {
  horeca:     'bg-metro-blue',
  trader:     'bg-metro-green',
  sco:        'bg-metro-orange',
  freelancer: 'bg-metro-red',
};

export default function BehaviorSummary() {
  const { data, isLoading, error } = useBehaviorSummary();

  if (isLoading) {
    return (
      <div className="glass rounded-2xl p-6">
        <div className="skeleton h-4 w-40 mb-4" />
        <div className="grid grid-cols-3 gap-4 mb-4">
          {[0, 1, 2].map(i => (
            <div key={i} className="glass rounded-xl p-4">
              <div className="skeleton h-3 w-16 mb-2" />
              <div className="skeleton h-7 w-20" />
            </div>
          ))}
        </div>
        <div className="skeleton h-3 w-56 mb-3" />
        {[0, 1, 2, 3].map(i => (
          <div key={i} className="skeleton h-4 w-full mb-2" />
        ))}
      </div>
    );
  }

  // 404 → neutral empty state, not an error
  if (error || !data) {
    return (
      <div className="glass rounded-2xl p-6">
        <h3 className="text-lg font-bold text-metro-gray-900 font-heading mb-2">
          Activitate Zilnica
        </h3>
        <p className="text-sm text-metro-gray-400">
          Nicio simulare disponibila — ruleaza pipeline-ul pentru a genera activitate.
        </p>
      </div>
    );
  }

  const totalOrders = Object.values(data.orders_by_segment).reduce((s, v) => s + v, 0) || 1;
  const segments = Object.entries(data.orders_by_segment).sort((a, b) => b[1] - a[1]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="glass rounded-2xl p-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-metro-gray-900 font-heading">
          Activitate Zilnica
        </h3>
        <span className="text-xs font-mono text-metro-gray-500 bg-metro-gray-100 px-2 py-1 rounded-lg">
          {data.run_date}
        </span>
      </div>

      {/* Top-3 KPI cards */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="bg-metro-blue/5 border border-metro-blue/20 rounded-xl p-3 text-center">
          <div className="text-xs text-metro-gray-500 uppercase tracking-wider mb-1">Comenzi</div>
          <div className="text-2xl font-bold text-metro-blue font-heading">
            {data.orders_generated.toLocaleString('ro-RO')}
          </div>
        </div>
        <div className="bg-metro-gray-50 border border-metro-gray-200 rounded-xl p-3 text-center">
          <div className="text-xs text-metro-gray-500 uppercase tracking-wider mb-1">Impresii</div>
          <div className="text-2xl font-bold text-metro-gray-900 font-heading">
            {data.impressions_shown.toLocaleString('ro-RO')}
          </div>
        </div>
        <div className="bg-metro-green/5 border border-metro-green/20 rounded-xl p-3 text-center">
          <div className="text-xs text-metro-gray-500 uppercase tracking-wider mb-1">Rascumparari</div>
          <div className="text-2xl font-bold text-metro-green font-heading">
            {data.redemptions_made.toLocaleString('ro-RO')}
          </div>
        </div>
      </div>

      {/* Secondary metrics */}
      <div className="flex items-center gap-3 text-sm text-metro-gray-600 mb-4 flex-wrap">
        <span>
          Rata rascumparare:{' '}
          <span className="font-semibold text-metro-gray-900">
            {(data.redemption_rate * 100).toFixed(2)}%
          </span>
        </span>
        <span className="text-metro-gray-300">•</span>
        <span>
          Cos mediu:{' '}
          <span className="font-semibold text-metro-gray-900">{data.avg_basket_size} buc</span>
        </span>
        {data.top_category && (
          <>
            <span className="text-metro-gray-300">•</span>
            <span>
              Categorie top:{' '}
              <span className="font-semibold text-metro-gray-900">
                {CATEGORY_DISPLAY[data.top_category] ?? data.top_category}
              </span>
            </span>
          </>
        )}
      </div>

      {/* Segment bars */}
      <div className="space-y-2">
        {segments.map(([seg, count]) => {
          const pct = Math.round((count / totalOrders) * 100);
          const barColor = SEGMENT_COLORS[seg] ?? 'bg-metro-gray-300';
          return (
            <div key={seg} className="flex items-center gap-3">
              <span className="text-xs text-metro-gray-600 w-24 flex-shrink-0">
                {BUSINESS_TYPE_DISPLAY[seg] ?? seg}
              </span>
              <div className="flex-1 bg-metro-gray-100 rounded-full h-2 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${pct}%` }}
                  transition={{ duration: 0.5, delay: 0.1 }}
                  className={`h-2 rounded-full ${barColor}`}
                />
              </div>
              <span className="text-xs text-metro-gray-500 w-8 text-right font-mono">{pct}%</span>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
}
