import { useMetrics } from '../../api/hooks';

export default function MetricsCards() {
  const { data: metricsData, isLoading } = useMetrics();

  let metrics: Record<string, number> = {};
  if (metricsData?.metadata) {
    try {
      metrics = typeof metricsData.metadata === 'string'
        ? JSON.parse(metricsData.metadata)
        : metricsData.metadata;
    } catch {
      // ignore
    }
  }

  const cards = [
    { label: 'NDCG@10', key: 'ndcg_at_k', format: (v: number) => v.toFixed(4), color: 'metro-blue' },
    { label: 'Precision@10', key: 'precision_at_k', format: (v: number) => v.toFixed(4), color: 'metro-blue' },
    { label: 'Recall@10', key: 'recall_at_k', format: (v: number) => v.toFixed(4), color: 'metro-blue' },
    { label: 'MRR', key: 'mrr', format: (v: number) => v.toFixed(4), color: 'metro-blue' },
    { label: 'Redemption Rate', key: 'redemption_rate_at_k', format: (v: number) => `${(v * 100).toFixed(1)}%`, color: 'metro-green' },
    { label: 'NDCG Lift vs Random', key: 'ndcg_lift', format: (v: number) => `${v.toFixed(2)}x`, color: 'metro-orange' },
  ];

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="glass rounded-xl p-4">
            <div className="skeleton h-3 w-20 mb-2" />
            <div className="skeleton h-6 w-16" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-bold text-metro-gray-900">Metrici Model</h3>
        {metricsData?.run_date && (
          <span className="text-xs text-metro-gray-500 font-mono">{metricsData.run_date}</span>
        )}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {cards.map((card) => {
          const value = metrics[card.key];
          return (
            <div key={card.key} className="glass rounded-xl p-4">
              <div className="text-xs text-metro-gray-500 uppercase tracking-wider mb-1">{card.label}</div>
              <div className={`text-xl font-bold text-${card.color}`}>
                {value !== undefined ? card.format(value) : '—'}
              </div>
              {/* Random baseline comparison */}
              {metrics[`random_${card.key}`] !== undefined && value !== undefined && (
                <div className="text-[10px] text-metro-gray-400 mt-1">
                  Random: {card.format(metrics[`random_${card.key}`])}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
