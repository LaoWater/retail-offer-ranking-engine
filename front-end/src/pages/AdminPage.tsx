import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  useHealth, useDbStats, usePipelineRuns,
  useSimulateBehavior, useRunMlPipeline, useSimulateWeek,
  useBehaviorSummary, useDriftLatest, useMetrics, useMetricsHistory,
} from '../api/hooks';
import { CATEGORY_DISPLAY, BUSINESS_TYPE_DISPLAY } from '../types/metro';
import CustomerExplorer from '../components/admin/CustomerExplorer';
import DatabaseStats from '../components/admin/DatabaseStats';

// ─── tiny shared tooltip ─────────────────────────────────────────────────────
function Tip({ text, children }: { text: string; children: React.ReactNode }) {
  const [show, setShow] = useState(false);
  return (
    <span className="relative inline-flex" onMouseEnter={() => setShow(true)} onMouseLeave={() => setShow(false)}>
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

function InfoIcon({ tip }: { tip: string }) {
  return (
    <Tip text={tip}>
      <svg className="w-4 h-4 text-metro-gray-400 hover:text-metro-blue cursor-help" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
      </svg>
    </Tip>
  );
}

// ─── section header ───────────────────────────────────────────────────────────
function SectionHeader({ label, sub, tip }: { label: string; sub: string; tip?: string }) {
  return (
    <div className="flex items-start gap-2 mb-4">
      <div>
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-bold text-metro-gray-900 font-heading">{label}</h3>
          {tip && <InfoIcon tip={tip} />}
        </div>
        <p className="text-xs text-metro-gray-500 mt-0.5">{sub}</p>
      </div>
    </div>
  );
}

// ─── run button ───────────────────────────────────────────────────────────────
function RunButton({
  onClick, disabled, pending, label, pendingLabel, variant = 'primary',
}: {
  onClick: () => void; disabled: boolean; pending: boolean;
  label: string; pendingLabel: string; variant?: 'primary' | 'outline' | 'ghost';
}) {
  const base = 'px-5 py-2.5 rounded-xl font-medium text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2';
  const styles = {
    primary: 'bg-metro-blue text-white hover:bg-metro-blue-dark',
    outline: 'border border-metro-blue text-metro-blue bg-white hover:bg-metro-blue/5',
    ghost:   'text-metro-gray-600 hover:bg-metro-gray-100',
  };
  return (
    <button onClick={onClick} disabled={disabled || pending} className={`${base} ${styles[variant]}`}>
      {pending ? (
        <>
          <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          {pendingLabel}
        </>
      ) : (
        <>
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
          </svg>
          {label}
        </>
      )}
    </button>
  );
}

// ─── feedback banner ──────────────────────────────────────────────────────────
function Feedback({ error, success }: { error?: string | null; success?: string | null }) {
  if (error) return (
    <div className="mt-3 p-3 bg-metro-red/10 text-metro-red text-sm rounded-lg flex items-center gap-2">
      <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
      </svg>
      {error}
    </div>
  );
  if (success) return (
    <div className="mt-3 p-3 bg-metro-green/10 text-metro-green text-sm rounded-lg flex items-center gap-2">
      <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      {success}
    </div>
  );
  return null;
}

// ─── SEGMENT COLORS ───────────────────────────────────────────────────────────
const SEG_COLORS: Record<string, string> = {
  horeca: 'bg-metro-blue', trader: 'bg-metro-green',
  sco: 'bg-metro-orange', freelancer: 'bg-metro-red',
};
const SEG_TEXT: Record<string, string> = {
  horeca: 'text-metro-blue', trader: 'text-metro-green',
  sco: 'text-metro-orange', freelancer: 'text-metro-red',
};

// ─── BEHAVIOR PANEL ───────────────────────────────────────────────────────────
function BehaviorPanel() {
  const simBehavior = useSimulateBehavior();
  const { data: behavior } = useBehaviorSummary();
  const isRunning = simBehavior.isPending;

  const totalOrders = behavior
    ? Object.values(behavior.orders_by_segment).reduce((s, v) => s + v, 0)
    : 0;

  return (
    <div className="glass rounded-2xl p-6">
      <SectionHeader
        label="Activitate Clienți"
        sub="Generează comenzi, impresii și rascumparări pentru ziua curentă — fara ML"
        tip={"Simuleaza ce se intampla in magazin:\nclienti cumpara, primesc notificari,\nrascumpara oferte. Fara reantrenare model."}
      />

      <div className="flex flex-wrap gap-3 mb-5">
        <RunButton
          onClick={() => simBehavior.mutate()}
          disabled={false}
          pending={isRunning}
          label="Simuleaza Comportament"
          pendingLabel="Simulare..."
          variant="primary"
        />
      </div>

      <Feedback
        error={simBehavior.error?.message}
        success={simBehavior.data ? `Comportament simulat pentru ${simBehavior.data.run_date}` : null}
      />

      {behavior && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
          {/* Date */}
          <div className="flex items-center justify-between mb-4 mt-4">
            <span className="text-xs text-metro-gray-500">Ultima simulare</span>
            <span className="text-xs font-mono text-metro-gray-700 bg-metro-gray-100 px-2 py-0.5 rounded">{behavior.run_date}</span>
          </div>

          {/* KPI row */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            {[
              { label: 'Comenzi', value: behavior.orders_generated.toLocaleString('ro-RO'), color: 'metro-blue' },
              { label: 'Impresii', value: behavior.impressions_shown.toLocaleString('ro-RO'), color: 'metro-gray-700' },
              { label: 'Rascumparari', value: behavior.redemptions_made.toLocaleString('ro-RO'), color: 'metro-green' },
            ].map(({ label, value, color }) => (
              <div key={label} className="bg-metro-gray-50 rounded-xl p-3 text-center">
                <div className="text-[10px] text-metro-gray-500 uppercase tracking-wider mb-1">{label}</div>
                <div className={`text-xl font-bold text-${color} font-heading`}>{value}</div>
              </div>
            ))}
          </div>

          {/* Secondary row */}
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-metro-gray-600 mb-4">
            <span>
              Conversie: <span className="font-semibold text-metro-gray-900">
                {behavior.impressions_shown > 0
                  ? `${(behavior.redemption_rate * 100).toFixed(2)}%`
                  : '—'}
              </span>
            </span>
            <span className="text-metro-gray-300">•</span>
            <span>Cos mediu: <span className="font-semibold text-metro-gray-900">{behavior.avg_basket_size} buc</span></span>
            {behavior.top_category && (
              <>
                <span className="text-metro-gray-300">•</span>
                <span>Top: <span className="font-semibold text-metro-gray-900">{CATEGORY_DISPLAY[behavior.top_category] ?? behavior.top_category}</span></span>
              </>
            )}
          </div>

          {/* Segment bars */}
          <div className="space-y-2">
            {Object.entries(behavior.orders_by_segment)
              .sort((a, b) => b[1] - a[1])
              .map(([seg, count]) => {
                const pct = totalOrders > 0 ? Math.round((count / totalOrders) * 100) : 0;
                return (
                  <div key={seg} className="flex items-center gap-3">
                    <span className="text-xs text-metro-gray-600 w-24 flex-shrink-0">{BUSINESS_TYPE_DISPLAY[seg] ?? seg}</span>
                    <div className="flex-1 bg-metro-gray-100 rounded-full h-2 overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.5 }}
                        className={`h-2 rounded-full ${SEG_COLORS[seg] ?? 'bg-metro-gray-400'}`}
                      />
                    </div>
                    <span className={`text-xs font-mono font-semibold w-10 text-right ${SEG_TEXT[seg] ?? 'text-metro-gray-500'}`}>{pct}%</span>
                    <span className="text-xs text-metro-gray-400 w-16 text-right">{count.toLocaleString('ro-RO')}</span>
                  </div>
                );
              })}
          </div>
        </motion.div>
      )}

      {!behavior && !isRunning && (
        <p className="text-sm text-metro-gray-400 mt-2">
          Nicio simulare disponibila — apasa butonul pentru a genera activitate.
        </p>
      )}
    </div>
  );
}

// ─── STEP INFO ────────────────────────────────────────────────────────────────
const STEP_INFO: Record<string, { label: string; desc: string }> = {
  features:   { label: 'Features',    desc: 'RFM, afinitate categorii, tier ratii, entropia cosului' },
  model:      { label: 'Model ML',    desc: 'Antrenare LightGBM / Logistic Regression sau incarcare model existent' },
  candidates: { label: 'Candidati',   desc: '~200 oferte candidate per client prin 7 strategii' },
  scoring:    { label: 'Scoring',     desc: 'Rancare candidati → top-10 recomandari per client' },
  drift:      { label: 'Drift (PSI)', desc: 'Detectie drift in distributia featuresurilor (Population Stability Index)' },
  evaluate:   { label: 'Evaluare',    desc: 'NDCG@10, Precision@10, Recall@10, MRR vs. baseline random' },
};

// ─── ML PIPELINE PANEL ────────────────────────────────────────────────────────
function MlPipelinePanel() {
  const runMl = useRunMlPipeline();
  const simWeek = useSimulateWeek();
  const { data: runs } = usePipelineRuns(56); // 8 days × 7 steps
  const { data: health } = useHealth();
  const isRunning = runMl.isPending || simWeek.isPending;

  // Group completed/failed runs by date, exclude behavior step
  const mlSteps = new Set(['features', 'model', 'candidates', 'scoring', 'drift', 'evaluate']);
  const byDate: Record<string, typeof runs> = {};
  runs?.filter(r => mlSteps.has(r.step)).forEach(r => {
    if (!byDate[r.run_date]) byDate[r.run_date] = [];
    byDate[r.run_date]!.push(r);
  });
  const sortedDates = Object.keys(byDate).sort().reverse();

  return (
    <div className="glass rounded-2xl p-6">
      <SectionHeader
        label="Pipeline ML"
        sub="Features → Model → Candidati → Scoring → Drift → Evaluare"
        tip={"Ruleaza pipeline-ul de ranking:\nrecalculeaza features din comenzile de azi,\nreantreaza sau incarca modelul,\ngenereaza top-10 recomandari per client."}
      />

      <div className="flex items-center gap-4 mb-5">
        {/* Last run + health */}
        <div>
          <div className="text-[10px] text-metro-gray-500 uppercase tracking-wider mb-0.5">Ultima rulare</div>
          <div className="text-lg font-bold text-metro-blue font-mono">{health?.last_run_date || '—'}</div>
        </div>
        <div className="h-8 w-px bg-metro-gray-200" />
        <div className="flex items-center gap-1.5">
          <div className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-metro-green' : 'bg-metro-red'}`} />
          <span className="text-sm text-metro-gray-600">{health?.status || '—'}</span>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 mb-2">
        <Tip text={"Ruleaza pipeline-ul ML pe datele\nde comportament deja simulate.\nFeatures → Model → Scoring → Drift → Eval"}>
          <RunButton
            onClick={() => runMl.mutate()}
            disabled={false}
            pending={runMl.isPending}
            label="Ruleaza Pipeline ML"
            pendingLabel="Pipeline in curs..."
            variant="primary"
          />
        </Tip>
        <Tip text={"Simuleaza 7 zile consecutive:\ncomportament + pipeline ML pentru fiecare zi.\nUtil pentru a vedea evolutia metricilor."}>
          <RunButton
            onClick={() => simWeek.mutate()}
            disabled={false}
            pending={simWeek.isPending}
            label="Simuleaza Saptamana"
            pendingLabel="Saptamana in curs..."
            variant="outline"
          />
        </Tip>
      </div>

      <Feedback
        error={(runMl.error || simWeek.error)?.message}
        success={
          runMl.data ? `Pipeline completat pentru ${runMl.data.run_date}` :
          simWeek.data ? `Saptamana simulata pana la ${simWeek.data.run_date}` : null
        }
      />

      {/* Pipeline history */}
      {sortedDates.length > 0 && (
        <div className="mt-5 space-y-3">
          <div className="text-xs font-semibold text-metro-gray-500 uppercase tracking-wider flex items-center gap-1.5">
            Istoric
            <InfoIcon tip="Fiecare zi: 6 pasi ML. Verde = completat, Rosu = esuat." />
          </div>

          {sortedDates.map(runDate => {
            const dateRuns = byDate[runDate]!;
            const allDone = dateRuns.every(r => r.status === 'completed');
            const hasFail = dateRuns.some(r => r.status === 'failed');
            const total = dateRuns.reduce((s, r) => s + (r.duration_seconds ?? 0), 0);
            const overallColor = hasFail ? 'bg-metro-red/5' : allDone ? 'bg-metro-green/5' : 'bg-metro-yellow/5';
            const badgeColor = hasFail ? 'bg-metro-red/15 text-metro-red' : allDone ? 'bg-metro-green/15 text-metro-green' : 'bg-metro-yellow/20 text-metro-yellow-dark';

            return (
              <div key={runDate} className="border border-metro-gray-100 rounded-xl overflow-hidden">
                {/* Date header */}
                <div className={`flex items-center justify-between px-4 py-2 ${overallColor}`}>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm font-bold text-metro-gray-900">{runDate}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${badgeColor}`}>
                      {hasFail ? 'erori' : allDone ? 'complet' : 'partial'}
                    </span>
                  </div>
                  <span className="text-[10px] text-metro-gray-400 font-mono">{total.toFixed(1)}s total</span>
                </div>

                {/* Step rows */}
                <div className="divide-y divide-metro-gray-50">
                  {dateRuns.map(run => {
                    const info = STEP_INFO[run.step];
                    // Parse inline result for evaluate step
                    let evalPreview: React.ReactNode = null;
                    if (run.step === 'evaluate' && run.status === 'completed' && run.metadata) {
                      try {
                        const m = JSON.parse(run.metadata);
                        evalPreview = (
                          <div className="flex gap-3 mt-1.5 flex-wrap">
                            {[
                              ['NDCG', m.ndcg_at_k?.toFixed(4)],
                              ['Prec', m.precision_at_k?.toFixed(4)],
                              ['MRR', m.mrr?.toFixed(4)],
                              ['Lift', m.ndcg_lift != null ? `${m.ndcg_lift.toFixed(2)}×` : null],
                            ].filter(([, v]) => v != null).map(([k, v]) => (
                              <span key={k} className="text-[10px] font-mono bg-metro-blue/8 text-metro-blue px-1.5 py-0.5 rounded">
                                {k}: {v}
                              </span>
                            ))}
                          </div>
                        );
                      } catch { /* ignore */ }
                    }
                    // Parse drift for inline preview
                    let driftPreview: React.ReactNode = null;
                    if (run.step === 'drift' && run.status === 'completed' && run.metadata) {
                      try {
                        const alerts = JSON.parse(run.metadata);
                        if (Array.isArray(alerts) && alerts.length > 0) {
                          const alertCount = alerts.filter((a: {severity: string}) => a.severity === 'alert').length;
                          const warnCount  = alerts.filter((a: {severity: string}) => a.severity === 'warn').length;
                          driftPreview = (
                            <div className="flex gap-2 mt-1.5">
                              {alertCount > 0 && <span className="text-[10px] px-1.5 py-0.5 rounded bg-metro-red/15 text-metro-red font-semibold">{alertCount} alert</span>}
                              {warnCount  > 0 && <span className="text-[10px] px-1.5 py-0.5 rounded bg-metro-orange/15 text-metro-orange font-semibold">{warnCount} warn</span>}
                              {alertCount === 0 && warnCount === 0 && <span className="text-[10px] px-1.5 py-0.5 rounded bg-metro-green/15 text-metro-green font-semibold">OK</span>}
                            </div>
                          );
                        }
                      } catch { /* ignore */ }
                    }

                    return (
                      <div key={run.run_id} className="px-4 py-2.5 hover:bg-metro-blue/2 transition-colors">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2.5 min-w-0">
                            <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                              run.status === 'completed' ? 'bg-metro-green' :
                              run.status === 'failed'    ? 'bg-metro-red'   : 'bg-metro-yellow'
                            }`} />
                            <Tip text={info?.desc ?? run.step}>
                              <span className="text-sm text-metro-gray-700 cursor-help">{info?.label ?? run.step}</span>
                            </Tip>
                          </div>
                          <div className="flex items-center gap-2 flex-shrink-0">
                            <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                              run.status === 'completed' ? 'bg-metro-green/10 text-metro-green' :
                              run.status === 'failed'    ? 'bg-metro-red/10 text-metro-red'     : 'bg-metro-yellow/20 text-metro-yellow-dark'
                            }`}>{run.status}</span>
                            <span className="text-[10px] text-metro-gray-400 font-mono w-14 text-right">
                              {run.duration_seconds != null ? `${run.duration_seconds.toFixed(1)}s` : '—'}
                            </span>
                          </div>
                        </div>
                        {evalPreview}
                        {driftPreview}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {sortedDates.length === 0 && !isRunning && (
        <p className="text-sm text-metro-gray-400 mt-4">Niciun run ML inregistrat.</p>
      )}
    </div>
  );
}

// ─── METRICS PANEL ────────────────────────────────────────────────────────────
function MetricsPanel() {
  const { data: latest, isLoading } = useMetrics();
  const { data: history } = useMetricsHistory(14);

  const m = latest?.metrics ?? {};

  const cards = [
    { key: 'ndcg_at_k',            label: 'NDCG@10',          fmt: (v: number) => v.toFixed(4),           color: 'text-metro-blue',   tip: 'Normalized Discounted Cumulative Gain\nCat de sus sunt ofertele relevante in top-10' },
    { key: 'precision_at_k',       label: 'Precision@10',     fmt: (v: number) => v.toFixed(4),           color: 'text-metro-blue',   tip: 'Din top-10, cate au fost intr-adevar rascumparate' },
    { key: 'recall_at_k',          label: 'Recall@10',        fmt: (v: number) => v.toFixed(4),           color: 'text-metro-blue',   tip: 'Din toate rascumpararile reale, cate au fost in top-10' },
    { key: 'mrr',                  label: 'MRR',              fmt: (v: number) => v.toFixed(4),           color: 'text-metro-blue',   tip: 'Mean Reciprocal Rank — pozitia primei oferte relevante' },
    { key: 'redemption_rate_at_k', label: 'Redemption Rate',  fmt: (v: number) => `${(v*100).toFixed(1)}%`, color: 'text-metro-green', tip: 'Rata de rascumparare pentru ofertele din top-10' },
    { key: 'ndcg_lift',            label: 'Lift vs Random',   fmt: (v: number) => `${v.toFixed(2)}×`,     color: 'text-metro-orange', tip: 'De cate ori e mai bun modelul fata de un ranking aleator.\n>1.0 = modelul adauga valoare reala' },
  ];

  if (isLoading) return (
    <div className="glass rounded-2xl p-6">
      <div className="skeleton h-5 w-40 mb-4" />
      <div className="grid grid-cols-3 gap-3">
        {Array.from({ length: 6 }).map((_, i) => <div key={i} className="skeleton h-16 rounded-xl" />)}
      </div>
    </div>
  );

  return (
    <div className="glass rounded-2xl p-6">
      <div className="flex items-center justify-between mb-4">
        <SectionHeader
          label="Metrici Model"
          sub="Offline evaluation pe rascumparari reale"
          tip="Calculat dupa fiecare run ML. Compara ranking-ul modelului cu redemptions reale din urmatoarele 7 zile."
        />
        {latest?.run_date && (
          <span className="text-[10px] font-mono text-metro-gray-500 bg-metro-gray-100 px-2 py-0.5 rounded">{latest.run_date}</span>
        )}
      </div>

      {Object.keys(m).length === 0 ? (
        <p className="text-sm text-metro-gray-400">Nicio evaluare disponibila — ruleaza pipeline-ul ML.</p>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-5">
            {cards.map((c, i) => {
              const val = m[c.key];
              const randKey = `random_${c.key}`;
              const randVal = m[randKey];
              return (
                <Tip key={c.key} text={c.tip}>
                  <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="glass rounded-xl p-3.5 cursor-help"
                  >
                    <div className="text-[10px] text-metro-gray-500 uppercase tracking-wider mb-1">{c.label}</div>
                    <div className={`text-xl font-bold font-mono ${c.color}`}>
                      {val != null ? c.fmt(val) : '—'}
                    </div>
                    {randVal != null && val != null && (
                      <div className="text-[10px] text-metro-gray-400 mt-0.5 font-mono">
                        Random: {c.fmt(randVal)}
                      </div>
                    )}
                  </motion.div>
                </Tip>
              );
            })}
          </div>

          {/* NDCG trend sparkline — simple bar chart */}
          {history && history.length > 1 && (
            <div>
              <div className="text-xs text-metro-gray-500 mb-2 flex items-center gap-1">
                Evolutie NDCG@10
                <InfoIcon tip="Un bar per zi de pipeline. Albastru = model, gri = random." />
              </div>
              <div className="flex items-end gap-1 h-14">
                {history.map((entry, i) => {
                  const val = entry.ndcg_at_k ?? 0;
                  const rand = (entry as Record<string, number>)['random_ndcg_at_k'] ?? 0;
                  const maxVal = Math.max(...history.map(e => e.ndcg_at_k ?? 0), 0.001);
                  const modelH = Math.max(4, Math.round((val / maxVal) * 48));
                  const randH  = Math.max(2, Math.round((rand / maxVal) * 48));
                  return (
                    <Tip key={i} text={`${entry.run_date}\nNDCG: ${val.toFixed(4)}\nRandom: ${rand.toFixed(4)}`}>
                      <div className="flex items-end gap-0.5 cursor-help">
                        <div style={{ height: randH }}  className="w-1.5 bg-metro-gray-300 rounded-t" />
                        <div style={{ height: modelH }} className="w-1.5 bg-metro-blue rounded-t" />
                      </div>
                    </Tip>
                  );
                })}
              </div>
              <div className="flex gap-3 mt-1.5">
                <span className="flex items-center gap-1 text-[10px] text-metro-gray-500">
                  <div className="w-2 h-2 rounded-sm bg-metro-blue" /> Model
                </span>
                <span className="flex items-center gap-1 text-[10px] text-metro-gray-500">
                  <div className="w-2 h-2 rounded-sm bg-metro-gray-300" /> Random
                </span>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ─── DRIFT PANEL ──────────────────────────────────────────────────────────────
function DriftPanel() {
  const { data: drift, isLoading } = useDriftLatest();

  if (isLoading) return (
    <div className="glass rounded-2xl p-6">
      <div className="skeleton h-5 w-40 mb-4" />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Array.from({ length: 8 }).map((_, i) => <div key={i} className="skeleton h-16 rounded-xl" />)}
      </div>
    </div>
  );

  const hasData = drift?.entries && drift.entries.length > 0;
  const allZero = hasData && drift!.entries.every(e => e.psi < 0.001);

  return (
    <div className="glass rounded-2xl p-6">
      <div className="flex items-start justify-between mb-4">
        <SectionHeader
          label="Drift Monitor (PSI)"
          sub="Distributia featuresurilor fata de baseline-ul de antrenare"
          tip={"Population Stability Index:\nPSI < 0.10 = OK\nPSI 0.10-0.25 = Warn\nPSI > 0.25 = Alert → reantrenare recomandata"}
        />
        {drift?.retrain_recommended && (
          <span className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-metro-red/10 text-metro-red text-xs font-semibold flex-shrink-0">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            Retrain Recomandat
          </span>
        )}
      </div>

      {!hasData && <p className="text-sm text-metro-gray-400">Nicio data de drift — ruleaza pipeline-ul ML.</p>}

      {hasData && allZero && (
        <p className="text-xs text-metro-gray-500 mb-3 bg-metro-blue/5 rounded-lg px-3 py-2">
          PSI = 0.000 pentru toate featurile — baseline si current sunt aceeasi zi (prima rulare). Valorile vor creste dupa mai multe zile simulate.
        </p>
      )}

      {hasData && (
        <>
          {drift!.run_date && (
            <div className="text-[10px] font-mono text-metro-gray-500 mb-3">Raport: {drift!.run_date}</div>
          )}
          {/* Bar chart — more interpretable than a grid of numbers */}
          <div className="space-y-2 mb-4">
            {drift!.entries.map(entry => {
              const pct = Math.min(100, (entry.psi / 0.30) * 100);
              const barColor =
                entry.severity === 'alert' ? 'bg-metro-red' :
                entry.severity === 'warn'  ? 'bg-metro-orange' : 'bg-metro-green';
              const textColor =
                entry.severity === 'alert' ? 'text-metro-red' :
                entry.severity === 'warn'  ? 'text-metro-orange' : 'text-metro-gray-600';
              return (
                <div key={entry.feature} className="flex items-center gap-3">
                  <span className="text-xs text-metro-gray-600 w-36 flex-shrink-0 truncate" title={entry.feature}>
                    {entry.feature.replace(/_/g, ' ')}
                  </span>
                  <div className="flex-1 bg-metro-gray-100 rounded-full h-2 overflow-hidden">
                    <div style={{ width: `${pct}%` }} className={`h-2 rounded-full transition-all ${barColor}`} />
                  </div>
                  <span className={`text-xs font-mono font-semibold w-14 text-right ${textColor}`}>
                    {entry.psi.toFixed(3)}
                  </span>
                  <span className={`text-[10px] font-semibold uppercase w-10 text-right ${textColor}`}>
                    {entry.severity}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Thresholds legend */}
          <div className="flex gap-4 text-[10px] text-metro-gray-500 pt-2 border-t border-metro-gray-100">
            <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-metro-green" /> OK (&lt;0.10)</span>
            <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-metro-orange" /> Warn (0.10–0.25)</span>
            <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-metro-red" /> Alert (&gt;0.25)</span>
          </div>
        </>
      )}
    </div>
  );
}

// ─── PAGE ─────────────────────────────────────────────────────────────────────
export default function AdminPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-metro-gray-900 font-heading">Admin ML Dashboard</h2>
        <p className="text-sm text-metro-gray-500 mt-1">
          Simuleaza comportament clienti → Ruleaza pipeline ML → Monitorizeaza metrici si drift
        </p>
      </div>

      {/* How it works — short explainer */}
      <div className="mb-6 bg-metro-blue/5 border border-metro-blue/15 rounded-2xl px-5 py-4">
        <div className="flex flex-wrap gap-6 text-sm text-metro-gray-700">
          <div className="flex items-start gap-2.5">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-metro-blue text-white text-[11px] font-bold flex items-center justify-center mt-0.5">1</span>
            <div>
              <div className="font-semibold text-metro-gray-900">Simuleaza Comportament</div>
              <div className="text-xs text-metro-gray-500 mt-0.5">Clientii cumpara, primesc notificari, rascumpara oferte. Fara ML.</div>
            </div>
          </div>
          <div className="flex items-start gap-2.5">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-metro-blue text-white text-[11px] font-bold flex items-center justify-center mt-0.5">2</span>
            <div>
              <div className="font-semibold text-metro-gray-900">Ruleaza Pipeline ML</div>
              <div className="text-xs text-metro-gray-500 mt-0.5">Recalculeaza features din datele noi, reantreaza modelul, genereaza top-10 pe maine.</div>
            </div>
          </div>
          <div className="flex items-start gap-2.5">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-metro-blue text-white text-[11px] font-bold flex items-center justify-center mt-0.5">3</span>
            <div>
              <div className="font-semibold text-metro-gray-900">Monitorizeaza</div>
              <div className="text-xs text-metro-gray-500 mt-0.5">NDCG, drift PSI, lift vs random — totul inline, interpretat direct.</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main column */}
        <div className="lg:col-span-2 space-y-6">
          <BehaviorPanel />
          <MlPipelinePanel />
          <MetricsPanel />
          <DriftPanel />
        </div>

        {/* Right column */}
        <div className="space-y-6 lg:sticky lg:top-6 lg:self-start">
          <DatabaseStats />
        </div>
      </div>

      {/* Customer Explorer — full width */}
      <div className="mt-6">
        <CustomerExplorer />
      </div>
    </div>
  );
}
