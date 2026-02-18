import { useState } from 'react';
import { motion } from 'framer-motion';
import { useDbStats } from '../../api/hooks';

/* ── tooltip (same pattern as PipelineControl) ────────────────── */
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

// Inline SVG icons for database stats
function StatsIcon({ type }: { type: string }) {
  const cls = "w-5 h-5 text-metro-blue";
  const props = { className: cls, fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", strokeWidth: 1.5 };

  switch (type) {
    case 'customers':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" /></svg>;
    case 'products':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" /></svg>;
    case 'offers':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z" /><path strokeLinecap="round" strokeLinejoin="round" d="M6 6h.008v.008H6V6z" /></svg>;
    case 'orders':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 00-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 00-16.536-1.84M7.5 14.25L5.106 5.272M6 20.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm12.75 0a.75.75 0 11-1.5 0 .75.75 0 011.5 0z" /></svg>;
    case 'recommendations':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" /></svg>;
    case 'database':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" /></svg>;
    default:
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" /></svg>;
  }
}

export default function DatabaseStats() {
  const { data: stats, isLoading } = useDbStats();

  const items = [
    { label: 'Clienti', value: stats?.total_customers?.toLocaleString('ro-RO'), icon: 'customers',
      tooltip: 'Clienti B2B inregistrati cu Metro Card\n(HoReCa, Traderi, SCO, Freelanceri)' },
    { label: 'Produse', value: stats?.total_products?.toLocaleString('ro-RO'), icon: 'products',
      tooltip: 'SKU-uri in catalog, fiecare cu\npret pe 2-3 trepte (Staffelpreise)' },
    { label: 'Oferte active', value: stats?.total_offers?.toLocaleString('ro-RO'), icon: 'offers',
      tooltip: 'Oferte promotionale active astazi\n(discount %, fixed, buy X get Y, etc.)' },
    { label: 'Comenzi', value: stats?.total_orders?.toLocaleString('ro-RO'), icon: 'orders',
      tooltip: 'Total comenzi din ultimele 6 luni\n(~87% business, ~13% individual)' },
    { label: 'Recomandari', value: stats?.total_recommendations?.toLocaleString('ro-RO'), icon: 'recommendations',
      tooltip: 'Top-10 oferte personalizate per client\ngenerate de pipeline-ul ML' },
    { label: 'DB Size', value: stats?.db_size_mb ? `${stats.db_size_mb} MB` : '—', icon: 'database',
      tooltip: 'Dimensiunea bazei de date SQLite\n(WAL mode, indexed)' },
  ];

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="glass rounded-xl p-4">
            <div className="skeleton h-3 w-16 mb-2" />
            <div className="skeleton h-6 w-20" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-lg font-bold text-metro-gray-900 mb-3">Baza de Date</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {items.map((item, i) => (
          <Tooltip key={item.label} text={item.tooltip}>
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: i * 0.06 }}
              className="glass rounded-xl p-4 cursor-help"
            >
              <div className="flex items-center gap-2 mb-1">
                <StatsIcon type={item.icon} />
                <span className="text-xs text-metro-gray-500 uppercase tracking-wider">{item.label}</span>
              </div>
              <div className="text-xl font-bold text-metro-gray-900 font-heading">{item.value || '—'}</div>
            </motion.div>
          </Tooltip>
        ))}
      </div>
    </div>
  );
}
