import { useCustomerProfile } from '../../api/hooks';
import { BUSINESS_TYPE_DISPLAY } from '../../types/metro';

interface Props {
  customerId: number;
}

export default function WelcomeBar({ customerId }: Props) {
  const { data: profile, isLoading } = useCustomerProfile(customerId);

  if (isLoading || !profile) {
    return (
      <div className="bg-white rounded-2xl p-6 shadow-sm">
        <div className="skeleton h-6 w-48 mb-2" />
        <div className="skeleton h-4 w-64" />
      </div>
    );
  }

  const f = profile.features;

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm">
      <h2 className="text-xl font-bold text-metro-gray-900">
        Bine ai venit, {profile.business_name}!
      </h2>

      <div className="flex flex-wrap items-center gap-2 mt-3">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-metro-blue/10 text-metro-blue text-sm font-medium">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
          {profile.business_subtype.replace(/_/g, ' ')} | {BUSINESS_TYPE_DISPLAY[profile.business_type]}
        </span>

        <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${
          profile.loyalty_tier === 'star' ? 'bg-metro-yellow/20 text-metro-yellow-dark' :
          profile.loyalty_tier === 'plus' ? 'bg-metro-blue/10 text-metro-blue' :
          'bg-metro-gray-100 text-metro-gray-500'
        }`}>
          {profile.loyalty_tier === 'star' && '★ '}
          {profile.loyalty_tier === 'plus' && '+ '}
          {profile.loyalty_tier.charAt(0).toUpperCase() + profile.loyalty_tier.slice(1)}
        </span>

        <span className="text-xs text-metro-gray-500 px-2">|</span>

        <span className="text-sm text-metro-gray-500">
          Card: {profile.metro_card_number}
        </span>
      </div>

      {f && (
        <div className="flex flex-wrap gap-4 mt-4 text-sm text-metro-gray-700">
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-metro-blue">{f.frequency}</span>
            <span className="text-metro-gray-500">comenzi</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-metro-blue">{Math.round(f.monetary).toLocaleString('ro-RO')}</span>
            <span className="text-metro-gray-500">RON total</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-metro-blue">{Math.round(f.avg_basket_size)}</span>
            <span className="text-metro-gray-500">articole/cos mediu</span>
          </div>
          {f.recency_days !== undefined && (
            <div className="flex items-center gap-1.5">
              <span className="font-semibold text-metro-blue">{Math.round(f.recency_days)}</span>
              <span className="text-metro-gray-500">zile de la ultima comanda</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
