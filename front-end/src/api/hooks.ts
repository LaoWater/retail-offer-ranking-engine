import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { get, post } from './client';
import type {
  RecommendationResponse,
  CustomerProfile,
  CustomerSample,
  ProductDetail,
  HealthResponse,
  PipelineRun,
  DriftReport,
  DbStats,
  PipelineSimulateResponse,
} from '../types/metro';

// ---- Customer ----

export function useCustomerSample(businessType?: string, limit = 20) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (businessType) params.set('business_type', businessType);
  return useQuery({
    queryKey: ['customers', 'sample', businessType, limit],
    queryFn: () => get<CustomerSample[]>(`/customers/sample?${params}`),
  });
}

export function useCustomerSearch(query: string) {
  return useQuery({
    queryKey: ['customers', 'search', query],
    queryFn: () => get<CustomerSample[]>(`/customers/search?q=${encodeURIComponent(query)}`),
    enabled: query.length >= 2,
  });
}

export function useCustomerProfile(customerId: number | null) {
  return useQuery({
    queryKey: ['customer', customerId],
    queryFn: () => get<CustomerProfile>(`/customers/${customerId}`),
    enabled: customerId !== null,
  });
}

// ---- Recommendations ----

export function useRecommendations(customerId: number | null) {
  return useQuery({
    queryKey: ['recommendations', customerId],
    queryFn: () => get<RecommendationResponse>(`/recommendations?customer_id=${customerId}`),
    enabled: customerId !== null,
  });
}

// ---- Products ----

export function useProductDetail(productId: number | null) {
  return useQuery({
    queryKey: ['product', productId],
    queryFn: () => get<ProductDetail>(`/products/${productId}`),
    enabled: productId !== null,
  });
}

// ---- Health & Stats ----

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => get<HealthResponse>('/health'),
    refetchInterval: 30000,
  });
}

export function useDbStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: () => get<DbStats>('/stats'),
  });
}

// ---- Pipeline ----

export function usePipelineRuns(limit = 10) {
  return useQuery({
    queryKey: ['pipeline', 'runs', limit],
    queryFn: () => get<PipelineRun[]>(`/pipeline/runs?limit=${limit}`),
  });
}

export function useSimulateDay() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => post<PipelineSimulateResponse>('/pipeline/simulate-day'),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['pipeline'] });
      qc.invalidateQueries({ queryKey: ['health'] });
      qc.invalidateQueries({ queryKey: ['stats'] });
      qc.invalidateQueries({ queryKey: ['recommendations'] });
      qc.invalidateQueries({ queryKey: ['drift'] });
      qc.invalidateQueries({ queryKey: ['metrics'] });
    },
  });
}

export function useSimulateWeek() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => post<PipelineSimulateResponse>('/pipeline/simulate-week'),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['pipeline'] });
      qc.invalidateQueries({ queryKey: ['health'] });
      qc.invalidateQueries({ queryKey: ['stats'] });
      qc.invalidateQueries({ queryKey: ['recommendations'] });
      qc.invalidateQueries({ queryKey: ['drift'] });
      qc.invalidateQueries({ queryKey: ['metrics'] });
    },
  });
}

// ---- Drift ----

export function useDriftLatest() {
  return useQuery({
    queryKey: ['drift', 'latest'],
    queryFn: () => get<DriftReport>('/drift/latest'),
  });
}

// ---- Metrics ----

export function useMetrics() {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: () => get<{ run_date: string; metadata: string }>('/metrics'),
  });
}
