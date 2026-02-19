// TypeScript interfaces matching the FastAPI response shapes

export interface OfferRecommendation {
  offer_id: number;
  product_id: number;
  product_name: string;
  subcategory: string | null;
  category: string;
  brand: string;
  offer_type: string;
  discount_value: number;
  tier1_price: number;
  campaign_type: string | null;
  score: number;
  rank: number;
  expiry_date: string;
}

export interface RecommendationResponse {
  customer_id: number;
  business_type: string;
  business_subtype: string;
  run_date: string;
  recommendations: OfferRecommendation[];
  generated_at: string;
}

export interface CustomerProfile {
  customer_id: number;
  business_name: string;
  business_type: string;
  business_subtype: string;
  tax_id: string | null;
  metro_card_number: string;
  card_issue_date: string;
  home_store_id: number;
  join_date: string;
  loyalty_tier: string;
  email_consent: boolean;
  sms_consent: boolean;
  app_registered: boolean;
  features?: CustomerFeatures;
}

export interface CustomerFeatures {
  customer_id: number;
  recency_days: number;
  frequency: number;
  monetary: number;
  promo_affinity: number;
  avg_basket_size: number;
  avg_basket_quantity: number;
  avg_order_value: number;
  category_entropy: number;
  top_3_categories: string;
  avg_discount_depth: number;
  tier2_purchase_ratio: number;
  tier3_purchase_ratio: number;
  avg_tier_savings_pct: number;
  fresh_category_ratio: number;
  business_order_ratio: number;
  preferred_shopping_day: number;
  days_between_visits_avg: number;
  loyalty_tier: string;
  business_type: string;
  business_subtype: string;
  reference_date: string;
}

export interface CustomerSample {
  customer_id: number;
  business_name: string;
  business_type: string;
  business_subtype: string;
  loyalty_tier: string;
  home_store_id: number;
}

export interface ProductDetail {
  product_id: number;
  name: string;
  category: string;
  subcategory: string | null;
  brand: string;
  is_own_brand: boolean;
  own_brand_name: string | null;
  tier1_price: number;
  tier2_price: number | null;
  tier2_min_qty: number | null;
  tier3_price: number | null;
  tier3_min_qty: number | null;
  margin: number;
  shelf_life_days: number;
  unit_type: string;
  pack_size: number;
  is_daily_price: boolean;
}

export interface HealthResponse {
  status: string;
  db_size_mb: number;
  last_run_date: string | null;
  total_customers: number;
  total_recommendations: number;
}

export interface PipelineRun {
  run_id: number;
  run_date: string;
  step: string;
  status: string;
  duration_seconds: number | null;
  metadata: string | null;
  created_at: string;
}

export interface DriftEntry {
  feature: string;
  psi: number;
  severity: 'ok' | 'warn' | 'alert';
}

export interface DriftReport {
  run_date: string;
  entries: DriftEntry[];
  retrain_recommended: boolean;
}

export interface DbStats {
  total_customers: number;
  total_products: number;
  total_offers: number;
  total_orders: number;
  total_recommendations: number;
  db_size_mb: number;
  last_run_date: string | null;
}

export interface MetricsData {
  run_date: string;
  metrics: Record<string, number>;
}

export interface PipelineSimulateResponse {
  status: string;
  run_date: string;
  results: Record<string, { status: string; duration: number }>;
}

export interface BehaviorSummary {
  run_date: string;
  orders_generated: number;
  impressions_shown: number;
  redemptions_made: number;
  redemption_rate: number;
  orders_by_segment: Record<string, number>;
  avg_basket_size: number;
  top_category: string | null;
}

// Display helpers
export const CATEGORY_DISPLAY: Record<string, string> = {
  meat_poultry: 'Carne',
  seafood: 'Peste',
  dairy_eggs: 'Lactate',
  fruits_vegetables: 'Fructe & Legume',
  beverages_non_alcoholic: 'Bauturi Nealcoolice',
  bakery_pastry: 'Panificatie',
  frozen_foods: 'Congelate',
  grocery_staples: 'Alimente de baza',
  beverages_alcoholic: 'Bauturi Alcoolice',
  confectionery_snacks: 'Dulciuri & Snacks',
  deli_charcuterie: 'Mezeluri',
  condiments_spices: 'Condimente',
  coffee_tea: 'Cafea & Ceai',
  cleaning_detergents: 'Curatenie',
  kitchen_utensils_tableware: 'Ustensile',
  horeca_equipment: 'Echipamente HoReCa',
  paper_packaging: 'Ambalaje',
  personal_care_hygiene: 'Cosmetice',
  household_goods: 'Produse casa',
  office_supplies: 'Birotica',
  electronics_small_appliances: 'Electronice',
};

export const BUSINESS_TYPE_DISPLAY: Record<string, string> = {
  horeca: 'HoReCa',
  trader: 'Revanzator',
  sco: 'SCO',
  freelancer: 'Freelancer',
};

export const UNIT_TYPE_DISPLAY: Record<string, string> = {
  buc: 'BUCATA',
  kg: 'KILOGRAM',
  l: 'LITRU',
};

export const OFFER_TYPE_DISPLAY: Record<string, string> = {
  percentage: 'Reducere %',
  fixed_amount: 'Reducere RON',
  buy_x_get_y: 'Cumpara X primesti Y',
  volume_bonus: 'Bonus volum',
  bundle: 'Pachet',
  free_gift: 'Cadou',
};
