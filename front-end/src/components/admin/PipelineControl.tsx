import { useState } from 'react';
import { useSimulateDay, useSimulateWeek, usePipelineRuns, useHealth } from '../../api/hooks';

/* ── tiny reusable tooltip ────────────────────────────────────── */
function Tooltip({ text, children }: { text: string; children: React.ReactNode }) {
  const [show, setShow] = useState(false);
  return (
    <span
      className="relative inline-flex"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      {show && (
        <span className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 text-xs text-white bg-metro-gray-900 rounded-lg shadow-lg whitespace-pre-line max-w-xs text-center pointer-events-none">
          {text}
          <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-metro-gray-900" />
        </span>
      )}
    </span>
  );
}

/* ── small info icon ──────────────────────────────────────────── */
function InfoIcon({ tooltip }: { tooltip: string }) {
  return (
    <Tooltip text={tooltip}>
      <svg className="w-4 h-4 text-metro-gray-400 hover:text-metro-blue cursor-help transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
      </svg>
    </Tooltip>
  );
}

/* ── step display names & descriptions ────────────────────────── */
const STEP_INFO: Record<string, { label: string; description: string }> = {
  features:   { label: 'Features',    description: 'Calcul RFM, afinitate categorii, ratii tier, etc. pentru toti clientii si ofertele' },
  model:      { label: 'Model',       description: 'Antrenare sau incarcare model ML (LightGBM / Logistic Regression)' },
  candidates: { label: 'Candidati',   description: 'Generare ~200 oferte candidate per client prin 7 strategii (afinitate, popularitate, repeat, etc.)' },
  scoring:    { label: 'Scoring',     description: 'Scorizare candidati cu modelul ML → top-10 recomandari per client' },
  drift:      { label: 'Drift (PSI)', description: 'Detectare drift in distributia feature-urilor fata de baseline (Population Stability Index)' },
  evaluate:   { label: 'Evaluare',    description: 'Metrici offline: NDCG@10, Precision@10, Recall@10, MRR vs. baseline random' },
};

export default function PipelineControl() {
  const { data: health } = useHealth();
  const { data: runs } = usePipelineRuns(30);
  const simulateDay = useSimulateDay();
  const simulateWeek = useSimulateWeek();

  const isRunning = simulateDay.isPending || simulateWeek.isPending;

  /* Group runs by date for a collapsed view */
  const runsByDate: Record<string, typeof runs> = {};
  runs?.forEach((run) => {
    if (!runsByDate[run.run_date]) runsByDate[run.run_date] = [];
    runsByDate[run.run_date]!.push(run);
  });

  return (
    <div className="space-y-4">
      {/* ── Control panel ────────────────────────────────── */}
      <div className="glass rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <h3 className="text-lg font-bold text-metro-gray-900 font-heading">Control Pipeline</h3>
          <InfoIcon tooltip={"Pipeline-ul zilnic recalculeaza\nfeatures → model → candidati →\nscoring → drift → evaluare"} />
        </div>

        <div className="flex items-center gap-4 mb-6">
          <div>
            <div className="text-xs text-metro-gray-500 uppercase tracking-wider flex items-center gap-1">
              Ultima rulare
              <InfoIcon tooltip="Data ultimului run complet al pipeline-ului de recomandari" />
            </div>
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

        {/* ── Action buttons with descriptions ───────────── */}
        <div className="flex flex-col sm:flex-row gap-3">
          <Tooltip text={"Ruleaza pipeline-ul complet pentru\nziua urmatoare (features → scoring).\nDureaza ~5 minute."}>
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
                  Simulare zi...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
                  </svg>
                  Simuleaza Ziua
                </>
              )}
            </button>
          </Tooltip>

          <Tooltip text={"Ruleaza pipeline-ul pentru 7 zile\nconsecutive. Util pentru a vedea\nevolutia metricilor in timp.\nDureaza ~30 minute."}>
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
                  Simulare saptamana...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 8.688c0-.864.933-1.405 1.683-.977l7.108 4.062a1.125 1.125 0 010 1.953l-7.108 4.062A1.125 1.125 0 013 16.81V8.688zM12.75 8.688c0-.864.933-1.405 1.683-.977l7.108 4.062a1.125 1.125 0 010 1.953l-7.108 4.062a1.125 1.125 0 01-1.683-.977V8.688z" />
                  </svg>
                  Simuleaza Saptamana
                </>
              )}
            </button>
          </Tooltip>
        </div>

        {/* ── Feedback ───────────────────────────────────── */}
        {(simulateDay.error || simulateWeek.error) && (
          <div className="mt-3 p-3 bg-metro-red/10 text-metro-red text-sm rounded-lg flex items-center gap-2">
            <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            {(simulateDay.error || simulateWeek.error)?.message}
          </div>
        )}

        {(simulateDay.data || simulateWeek.data) && (
          <div className="mt-3 p-3 bg-metro-green/10 text-metro-green text-sm rounded-lg flex items-center gap-2">
            <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Pipeline completat pentru {(simulateDay.data || simulateWeek.data)?.run_date}
          </div>
        )}
      </div>

      {/* ── Pipeline history — grouped by date ────────────── */}
      <div className="glass rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-3">
          <h4 className="text-sm font-bold text-metro-gray-900 font-heading">Istoric Pipeline</h4>
          <InfoIcon tooltip={"Fiecare zi ruleaza 6 pasi secventiali.\nVerde = completat, Rosu = esuat.\nDurata este per pas."} />
        </div>

        {Object.keys(runsByDate).length === 0 ? (
          <div className="py-6 text-center text-metro-gray-400 text-sm">
            Niciun run inregistrat
          </div>
        ) : (
          <div className="space-y-3">
            {Object.entries(runsByDate).map(([runDate, dateRuns]) => {
              const allCompleted = dateRuns!.every(r => r.status === 'completed');
              const hasFailed = dateRuns!.some(r => r.status === 'failed');
              const totalDuration = dateRuns!.reduce((sum, r) => sum + (r.duration_seconds || 0), 0);

              return (
                <div key={runDate} className="border border-metro-gray-100 rounded-xl overflow-hidden">
                  {/* Date header row */}
                  <div className={`flex items-center justify-between px-4 py-2.5 ${
                    hasFailed ? 'bg-metro-red/5' : allCompleted ? 'bg-metro-green/5' : 'bg-metro-yellow/5'
                  }`}>
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-sm font-bold text-metro-gray-900">{runDate}</span>
                      <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${
                        hasFailed ? 'bg-metro-red/15 text-metro-red' :
                        allCompleted ? 'bg-metro-green/15 text-metro-green' :
                        'bg-metro-yellow/20 text-metro-yellow-dark'
                      }`}>
                        {hasFailed ? 'cu erori' : allCompleted ? 'complet' : 'in curs'}
                      </span>
                    </div>
                    <Tooltip text="Durata totala a tuturor pasilor">
                      <span className="text-xs text-metro-gray-500 font-mono">
                        {totalDuration > 0 ? `${totalDuration.toFixed(1)}s total` : '—'}
                      </span>
                    </Tooltip>
                  </div>

                  {/* Step rows */}
                  <div className="divide-y divide-metro-gray-50">
                    {dateRuns!.map((run) => {
                      const info = STEP_INFO[run.step];
                      return (
                        <div
                          key={run.run_id}
                          className="flex items-center justify-between px-4 py-2 hover:bg-metro-blue/3 transition-colors group"
                        >
                          <div className="flex items-center gap-3 min-w-0">
                            {/* Status dot */}
                            <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                              run.status === 'completed' ? 'bg-metro-green' :
                              run.status === 'failed' ? 'bg-metro-red' :
                              'bg-metro-yellow'
                            }`} />

                            <Tooltip text={info?.description || run.step}>
                              <span className="text-sm text-metro-gray-700 cursor-help">
                                {info?.label || run.step}
                              </span>
                            </Tooltip>
                          </div>

                          <div className="flex items-center gap-3">
                            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                              run.status === 'completed' ? 'bg-metro-green/10 text-metro-green' :
                              run.status === 'failed' ? 'bg-metro-red/10 text-metro-red' :
                              'bg-metro-yellow/20 text-metro-yellow-dark'
                            }`}>
                              {run.status}
                            </span>
                            <span className="text-xs text-metro-gray-400 font-mono w-16 text-right">
                              {run.duration_seconds ? `${run.duration_seconds.toFixed(1)}s` : '—'}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
