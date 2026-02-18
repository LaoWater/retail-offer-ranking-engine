import { useState } from 'react';
import { motion } from 'framer-motion';
import { useMetrics } from '../../api/hooks';

/* ── tooltip ──────────────────────────────────────────────────── */
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

function InfoIcon({ tooltip }: { tooltip: string }) {
  return (
    <Tooltip text={tooltip}>
      <svg className="w-4 h-4 text-metro-gray-400 hover:text-metro-blue cursor-help transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
      </svg>
    </Tooltip>
  );
}

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
    { label: 'NDCG@10', key: 'ndcg_at_k', format: (v: number) => v.toFixed(4), color: 'metro-blue',
      tooltip: 'Normalized Discounted Cumulative Gain\nMasoara calitatea ranking-ului:\ncat de sus sunt ofertele relevante' },
    { label: 'Precision@10', key: 'precision_at_k', format: (v: number) => v.toFixed(4), color: 'metro-blue',
      tooltip: 'Din top-10 recomandate, cate au\nfost intr-adevar rascumparate' },
    { label: 'Recall@10', key: 'recall_at_k', format: (v: number) => v.toFixed(4), color: 'metro-blue',
      tooltip: 'Din toate rascumpararile reale,\ncate au fost in top-10' },
    { label: 'MRR', key: 'mrr', format: (v: number) => v.toFixed(4), color: 'metro-blue',
      tooltip: 'Mean Reciprocal Rank\nPozitia medie a primei oferte\nrelevante in ranking' },
    { label: 'Redemption Rate', key: 'redemption_rate_at_k', format: (v: number) => `${(v * 100).toFixed(1)}%`, color: 'metro-green',
      tooltip: 'Rata de rascumparare a ofertelor\ndin top-10 recomandate' },
    { label: 'NDCG Lift vs Random', key: 'ndcg_lift', format: (v: number) => `${v.toFixed(2)}x`, color: 'metro-orange',
      tooltip: 'De cate ori e mai bun modelul ML\nfata de un ranking aleatoriu.\n>1.0 = modelul adauga valoare' },
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
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-bold text-metro-gray-900 font-heading">Metrici Model</h3>
          <InfoIcon tooltip={"Metrici offline calculate pe baza\nrascumpararilor reale vs. ranking-ul\ngenerat de model. Evaluare pe ultimul run."} />
        </div>
        {metricsData?.run_date && (
          <span className="text-xs text-metro-gray-500 font-mono">{metricsData.run_date}</span>
        )}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {cards.map((card, i) => {
          const value = metrics[card.key];
          return (
            <Tooltip key={card.key} text={card.tooltip}>
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: i * 0.06 }}
                className="glass rounded-xl p-4 cursor-help"
              >
                <div className="text-xs text-metro-gray-500 uppercase tracking-wider mb-1">{card.label}</div>
                <div className={`text-xl font-bold text-${card.color} font-mono`}>
                  {value !== undefined ? card.format(value) : '—'}
                </div>
                {metrics[`random_${card.key}`] !== undefined && value !== undefined && (
                  <div className="text-[10px] text-metro-gray-400 mt-1 font-mono">
                    Random: {card.format(metrics[`random_${card.key}`])}
                  </div>
                )}
              </motion.div>
            </Tooltip>
          );
        })}
      </div>
    </div>
  );
}
