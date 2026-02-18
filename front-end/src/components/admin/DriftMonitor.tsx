import { useDriftLatest } from '../../api/hooks';

export default function DriftMonitor() {
  const { data: drift, isLoading } = useDriftLatest();

  if (isLoading) {
    return (
      <div className="glass rounded-2xl p-6">
        <div className="skeleton h-5 w-32 mb-4" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="skeleton h-16 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="glass rounded-2xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-metro-gray-900 font-heading">Drift Monitor (PSI)</h3>
        {drift?.retrain_recommended && (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-metro-red/10 text-metro-red text-xs font-semibold">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            Retrain Recomandat
          </span>
        )}
      </div>

      {drift?.entries && drift.entries.length > 0 ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {drift.entries.map((entry) => (
            <div
              key={entry.feature}
              className={`rounded-xl p-3 border-l-4 border ${
                entry.severity === 'alert' ? 'border-l-metro-red border-metro-red/20 bg-metro-red/5' :
                entry.severity === 'warn' ? 'border-l-metro-orange border-metro-orange/20 bg-metro-orange/5' :
                'border-l-metro-green border-metro-green/20 bg-metro-green/5'
              }`}
            >
              <div className="text-xs text-metro-gray-500 truncate mb-1">
                {entry.feature.replace(/_/g, ' ')}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-lg font-bold font-mono">
                  {entry.psi.toFixed(3)}
                </span>
                <span className={`text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded ${
                  entry.severity === 'alert' ? 'bg-metro-red/20 text-metro-red' :
                  entry.severity === 'warn' ? 'bg-metro-orange/20 text-metro-orange' :
                  'bg-metro-green/20 text-metro-green'
                }`}>
                  {entry.severity}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-metro-gray-500">Nu exista date de drift disponibile</p>
      )}

      {/* Legend */}
      <div className="flex gap-4 mt-4 text-[10px] text-metro-gray-500">
        <span className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-metro-green" /> OK (&lt;0.10)
        </span>
        <span className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-metro-orange" /> Warn (0.10-0.25)
        </span>
        <span className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-metro-red" /> Alert (&gt;0.25)
        </span>
      </div>
    </div>
  );
}
