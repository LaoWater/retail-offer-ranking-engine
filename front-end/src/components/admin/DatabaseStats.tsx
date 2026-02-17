import { useDbStats } from '../../api/hooks';

export default function DatabaseStats() {
  const { data: stats, isLoading } = useDbStats();

  const items = [
    { label: 'Clienti', value: stats?.total_customers?.toLocaleString('ro-RO'), icon: '👥' },
    { label: 'Produse', value: stats?.total_products?.toLocaleString('ro-RO'), icon: '📦' },
    { label: 'Oferte active', value: stats?.total_offers?.toLocaleString('ro-RO'), icon: '🏷️' },
    { label: 'Comenzi', value: stats?.total_orders?.toLocaleString('ro-RO'), icon: '🛒' },
    { label: 'Recomandari', value: stats?.total_recommendations?.toLocaleString('ro-RO'), icon: '⭐' },
    { label: 'DB Size', value: stats?.db_size_mb ? `${stats.db_size_mb} MB` : '—', icon: '💾' },
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
        {items.map((item) => (
          <div key={item.label} className="glass rounded-xl p-4">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg">{item.icon}</span>
              <span className="text-xs text-metro-gray-500 uppercase tracking-wider">{item.label}</span>
            </div>
            <div className="text-xl font-bold text-metro-gray-900">{item.value || '—'}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
