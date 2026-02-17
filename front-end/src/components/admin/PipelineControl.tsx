import { useSimulateDay, useSimulateWeek, usePipelineRuns, useHealth } from '../../api/hooks';

export default function PipelineControl() {
  const { data: health } = useHealth();
  const { data: runs } = usePipelineRuns(10);
  const simulateDay = useSimulateDay();
  const simulateWeek = useSimulateWeek();

  const isRunning = simulateDay.isPending || simulateWeek.isPending;

  return (
    <div className="space-y-4">
      {/* Current state */}
      <div className="glass rounded-2xl p-6">
        <h3 className="text-lg font-bold text-metro-gray-900 mb-4">Control Pipeline</h3>

        <div className="flex items-center gap-4 mb-6">
          <div>
            <div className="text-xs text-metro-gray-500 uppercase tracking-wider">Data curenta</div>
            <div className="text-2xl font-bold text-metro-blue font-mono">
              {health?.last_run_date || '—'}
            </div>
          </div>
          <div className="h-10 w-px bg-metro-gray-200" />
          <div>
            <div className="text-xs text-metro-gray-500 uppercase tracking-wider">Status</div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-metro-green' : 'bg-metro-red'}`} />
              <span className="text-sm font-medium">{health?.status || 'unknown'}</span>
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex gap-3">
          <button
            onClick={() => simulateDay.mutate()}
            disabled={isRunning}
            className="px-6 py-2.5 bg-metro-blue text-white rounded-xl font-medium text-sm hover:bg-metro-blue-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {simulateDay.isPending ? (
              <>
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Simulare...
              </>
            ) : (
              'Simuleaza Ziua'
            )}
          </button>
          <button
            onClick={() => simulateWeek.mutate()}
            disabled={isRunning}
            className="px-6 py-2.5 bg-white text-metro-blue border border-metro-blue rounded-xl font-medium text-sm hover:bg-metro-blue/5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {simulateWeek.isPending ? (
              <>
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Simulare...
              </>
            ) : (
              'Simuleaza Saptamana'
            )}
          </button>
        </div>

        {/* Error display */}
        {(simulateDay.error || simulateWeek.error) && (
          <div className="mt-3 p-3 bg-metro-red/10 text-metro-red text-sm rounded-lg">
            {(simulateDay.error || simulateWeek.error)?.message}
          </div>
        )}

        {/* Success display */}
        {(simulateDay.data || simulateWeek.data) && (
          <div className="mt-3 p-3 bg-metro-green/10 text-metro-green text-sm rounded-lg">
            Pipeline completat pentru {(simulateDay.data || simulateWeek.data)?.run_date}
          </div>
        )}
      </div>

      {/* Pipeline run log */}
      <div className="glass rounded-2xl p-6">
        <h4 className="text-sm font-bold text-metro-gray-900 mb-3">Istoric pipeline</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-metro-gray-500 text-xs uppercase tracking-wider">
                <th className="pb-2 pr-4">Data</th>
                <th className="pb-2 pr-4">Pas</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 text-right">Durata</th>
              </tr>
            </thead>
            <tbody>
              {runs?.map((run) => (
                <tr key={run.run_id} className="border-t border-metro-gray-100">
                  <td className="py-2 pr-4 font-mono text-xs">{run.run_date}</td>
                  <td className="py-2 pr-4">{run.step}</td>
                  <td className="py-2 pr-4">
                    <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${
                      run.status === 'completed' ? 'bg-metro-green/10 text-metro-green' :
                      run.status === 'failed' ? 'bg-metro-red/10 text-metro-red' :
                      'bg-metro-yellow/20 text-metro-yellow-dark'
                    }`}>
                      {run.status}
                    </span>
                  </td>
                  <td className="py-2 text-right text-metro-gray-500 font-mono text-xs">
                    {run.duration_seconds ? `${run.duration_seconds.toFixed(1)}s` : '—'}
                  </td>
                </tr>
              ))}
              {(!runs || runs.length === 0) && (
                <tr>
                  <td colSpan={4} className="py-4 text-center text-metro-gray-400">
                    Niciun run inregistrat
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
