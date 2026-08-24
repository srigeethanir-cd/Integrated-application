import { safeFetch, API_BASE } from './client';

export const traceabilityApi = {
  getTraceability: () =>
    safeFetch<any>(`${API_BASE}/api/v1/project/traceability`),
};
