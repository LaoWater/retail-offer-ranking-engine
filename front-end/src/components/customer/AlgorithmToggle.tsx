import { useMetrics } from '../../api/hooks';

export default function AlgorithmToggle() {
  const { data: metricsData } = useMetrics();

  let auc = '—';
  if (metricsData?.metadata) {
    try {
      const parsed = typeof metricsData.metadata === 'string'
        ? JSON.parse(metricsData.metadata)
        : metricsData.metadata;
      if (parsed?.ndcg_at_k) {
        auc = `NDCG@10: ${parsed.ndcg_at_k}`;
      }
    } catch {
      // ignore
    }
  }

  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-metro-gray-100">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-metro-green animate-pulse" />
            <span className="text-sm font-semibold text-metro-gray-900">
              Phase 1 — ML Clasic (LightGBM)
            </span>
          </div>
          <span className="text-xs px-2 py-0.5 rounded-full bg-metro-green/10 text-metro-green font-medium">
            Activ
          </span>
        </div>

        <div className="flex items-center gap-4">
          <span className="text-xs text-metro-gray-500 font-mono">{auc}</span>
          <div className="flex items-center gap-1 text-xs text-metro-gray-400">
            <span className="hidden sm:inline">Phase 2 — Deep Learning</span>
            <span className="px-2 py-0.5 rounded-full bg-metro-gray-100 text-metro-gray-400 text-[10px]">
              In curand
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
