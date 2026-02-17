import { useState, useRef, useEffect } from 'react';
import { useCustomerSample, useCustomerSearch } from '../../api/hooks';
import { BUSINESS_TYPE_DISPLAY } from '../../types/metro';

interface Props {
  selectedId: number | null;
  onSelect: (id: number) => void;
}

export default function CustomerSelector({ selectedId, onSelect }: Props) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const { data: samples } = useCustomerSample(undefined, 30);
  const { data: searchResults } = useCustomerSearch(query);

  const customers = query.length >= 2 ? searchResults : samples;

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const selected = customers?.find((c) => c.customer_id === selectedId);

  return (
    <div ref={ref} className="relative w-full max-w-md">
      <div
        className="flex items-center bg-white rounded-xl border border-metro-gray-200 px-4 py-2.5 cursor-pointer hover:border-metro-blue-light transition-colors shadow-sm"
        onClick={() => setOpen(!open)}
      >
        <svg className="w-5 h-5 text-metro-gray-400 mr-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>

        {open ? (
          <input
            type="text"
            className="flex-1 outline-none text-sm bg-transparent"
            placeholder="Cauta client dupa nume..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
        ) : (
          <span className="flex-1 text-sm truncate">
            {selected ? (
              <span className="flex items-center gap-2">
                <span className="font-medium">{selected.business_name}</span>
                <span className="text-xs px-1.5 py-0.5 rounded bg-metro-blue/10 text-metro-blue">
                  {BUSINESS_TYPE_DISPLAY[selected.business_type] || selected.business_type}
                </span>
              </span>
            ) : (
              <span className="text-metro-gray-400">Selecteaza un client...</span>
            )}
          </span>
        )}

        <svg className={`w-4 h-4 text-metro-gray-400 ml-2 transition-transform ${open ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      {open && customers && customers.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-xl border border-metro-gray-200 shadow-xl max-h-80 overflow-y-auto z-50">
          {customers.map((c) => (
            <button
              key={c.customer_id}
              className={`w-full text-left px-4 py-3 hover:bg-metro-gray-50 transition-colors flex items-center justify-between border-b border-metro-gray-100 last:border-0 ${
                c.customer_id === selectedId ? 'bg-metro-blue/5' : ''
              }`}
              onClick={() => {
                onSelect(c.customer_id);
                setOpen(false);
                setQuery('');
              }}
            >
              <div>
                <div className="text-sm font-medium text-metro-gray-900">{c.business_name}</div>
                <div className="text-xs text-metro-gray-500 mt-0.5">
                  {c.business_subtype} | ID: {c.customer_id}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs px-1.5 py-0.5 rounded bg-metro-blue/10 text-metro-blue">
                  {BUSINESS_TYPE_DISPLAY[c.business_type] || c.business_type}
                </span>
                <span className={`text-xs px-1.5 py-0.5 rounded ${
                  c.loyalty_tier === 'star' ? 'bg-metro-yellow/20 text-metro-yellow-dark' :
                  c.loyalty_tier === 'plus' ? 'bg-metro-blue/10 text-metro-blue' :
                  'bg-metro-gray-100 text-metro-gray-500'
                }`}>
                  {c.loyalty_tier}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
