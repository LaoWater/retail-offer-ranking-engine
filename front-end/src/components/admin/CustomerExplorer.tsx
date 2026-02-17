import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCustomerSample, useCustomerSearch } from '../../api/hooks';
import { BUSINESS_TYPE_DISPLAY } from '../../types/metro';

export default function CustomerExplorer() {
  const [filter, setFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const navigate = useNavigate();

  const { data: samples } = useCustomerSample(typeFilter || undefined, 50);
  const { data: searchResults } = useCustomerSearch(filter);

  const customers = filter.length >= 2 ? searchResults : samples;

  return (
    <div className="glass rounded-2xl p-6">
      <h3 className="text-lg font-bold text-metro-gray-900 mb-4">Explorer Clienti</h3>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <input
          type="text"
          placeholder="Cauta dupa nume..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="flex-1 px-4 py-2 rounded-lg border border-metro-gray-200 text-sm outline-none focus:border-metro-blue-light"
        />
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-4 py-2 rounded-lg border border-metro-gray-200 text-sm outline-none focus:border-metro-blue-light bg-white"
        >
          <option value="">Toate tipurile</option>
          <option value="horeca">HoReCa</option>
          <option value="trader">Revanzatori</option>
          <option value="sco">SCO</option>
          <option value="freelancer">Freelanceri</option>
        </select>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-metro-gray-500 text-xs uppercase tracking-wider">
              <th className="pb-2 pr-3">ID</th>
              <th className="pb-2 pr-3">Nume</th>
              <th className="pb-2 pr-3">Tip</th>
              <th className="pb-2 pr-3">Subtip</th>
              <th className="pb-2 pr-3">Tier</th>
              <th className="pb-2"></th>
            </tr>
          </thead>
          <tbody>
            {customers?.slice(0, 20).map((c) => (
              <tr
                key={c.customer_id}
                className="border-t border-metro-gray-100 hover:bg-metro-blue/3 cursor-pointer"
                onClick={() => navigate(`/?customer=${c.customer_id}`)}
              >
                <td className="py-2.5 pr-3 font-mono text-xs text-metro-gray-500">{c.customer_id}</td>
                <td className="py-2.5 pr-3 font-medium">{c.business_name}</td>
                <td className="py-2.5 pr-3">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-metro-blue/10 text-metro-blue">
                    {BUSINESS_TYPE_DISPLAY[c.business_type] || c.business_type}
                  </span>
                </td>
                <td className="py-2.5 pr-3 text-metro-gray-500 text-xs">{c.business_subtype}</td>
                <td className="py-2.5 pr-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    c.loyalty_tier === 'star' ? 'bg-metro-yellow/20 text-metro-yellow-dark' :
                    c.loyalty_tier === 'plus' ? 'bg-metro-blue/10 text-metro-blue' :
                    'bg-metro-gray-100 text-metro-gray-500'
                  }`}>
                    {c.loyalty_tier}
                  </span>
                </td>
                <td className="py-2.5">
                  <svg className="w-4 h-4 text-metro-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {(!customers || customers.length === 0) && (
          <div className="text-center py-8 text-metro-gray-400 text-sm">
            Niciun client gasit
          </div>
        )}
      </div>
    </div>
  );
}
