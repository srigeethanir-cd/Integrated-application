import { safeFetch, API_BASE } from './client';

export const validationApi = {
  /** Validation summary — uses the /api/v1 workspace router. */
  getSummary: () =>
    safeFetch<any>(`${API_BASE}/api/v1/workspace/validation-summary`),
};
